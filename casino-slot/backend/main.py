import json
from datetime import datetime
from typing import List
import os
import hashlib
import secrets

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Base, engine, get_db, SessionLocal
from models import User, Spin, SessionData, ProvablyFairState
from slot_engine import provably_fair_spin_reels, calculate_win
from slot_services import (
    get_reels_matrix_for_bet,
    acquire_spin_lock,
    release_spin_lock,
)
from integrations import get_redis, publish_spin_event

# Password hashing
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Casino Slot Backend", version="0.1.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/app",
    StaticFiles(directory="static", html=True),
    name="frontend",
)

app.mount(
    "/music",
    StaticFiles(directory="music"),
    name="music",
)


@app.get("/", response_class=HTMLResponse)
async def root_page() -> HTMLResponse:
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
          <meta charset="UTF-8" />
          <title>Dazino Casino</title>
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <style>
            * {
              box-sizing: border-box;
              margin: 0;
              padding: 0;
            }
            
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
              background: linear-gradient(135deg, #1e3a8a 0%, #312e81 50%, #1e1b4b 100%);
              min-height: 100vh;
              display: flex;
              align-items: center;
              justify-content: center;
              padding: 20px;
              color: white;
            }
            
            .auth-container {
              display: flex;
              justify-content: center;
              align-items: center;
              min-height: 100vh;
              width: 100%;
            }

            .auth-card {
              background: rgba(30, 41, 59, 0.95);
              backdrop-filter: blur(20px);
              border-radius: 24px;
              padding: 48px;
              box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
              border: 1px solid rgba(148, 163, 184, 0.2);
              width: 100%;
              max-width: 420px;
            }
            
            .auth-card h2 {
              text-align: center;
              margin-bottom: 32px;
              font-size: 36px;
              font-weight: 700;
              color: #f1f5f9;
              text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            
            .form-group {
              margin-bottom: 24px;
            }
            
            .form-group label {
              display: block;
              margin-bottom: 8px;
              font-weight: 600;
              font-size: 15px;
              color: #e2e8f0;
            }
            
            .auth-input {
              width: 100%;
              padding: 16px 20px;
              border: 2px solid rgba(148, 163, 184, 0.3);
              border-radius: 16px;
              background: rgba(15, 23, 42, 0.8);
              color: #f1f5f9;
              font-size: 16px;
              outline: none;
              transition: all 0.3s ease;
            }
            
            .auth-input:focus {
              border-color: #3b82f6;
              background: rgba(15, 23, 42, 0.9);
              box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
            }
            
            .auth-input::placeholder {
              color: #94a3b8;
            }
            
            .auth-button {
              width: 100%;
              padding: 18px 24px;
              background: linear-gradient(135deg, #3b82f6, #2563eb);
              border: none;
              border-radius: 16px;
              color: white;
              font-size: 18px;
              font-weight: 700;
              cursor: pointer;
              transition: all 0.3s ease;
              text-transform: uppercase;
              letter-spacing: 1.5px;
              margin-bottom: 20px;
              box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
            }
            
            .auth-button:hover:not(:disabled) {
              transform: translateY(-2px);
              box-shadow: 0 15px 40px rgba(59, 130, 246, 0.4);
              background: linear-gradient(135deg, #2563eb, #1d4ed8);
            }
            
            .auth-button:disabled {
              opacity: 0.5;
              cursor: not-allowed;
              transform: none;
            }
            
            .auth-switch {
              width: 100%;
              padding: 16px;
              background: transparent;
              border: 2px solid rgba(148, 163, 184, 0.3);
              border-radius: 16px;
              color: #e2e8f0;
              font-size: 15px;
              cursor: pointer;
              transition: all 0.3s ease;
              font-weight: 600;
            }
            
            .auth-switch:hover {
              background: rgba(59, 130, 246, 0.1);
              border-color: rgba(59, 130, 246, 0.5);
            }
            
            .error {
              color: #ef4444;
              font-size: 15px;
              text-align: center;
              margin-top: 12px;
              padding: 12px 16px;
              background: rgba(239, 68, 68, 0.15);
              border-radius: 12px;
              border: 1px solid rgba(239, 68, 68, 0.3);
              display: none;
              font-weight: 500;
            }
            
            .success {
              color: #10b981;
              font-size: 15px;
              text-align: center;
              margin-top: 12px;
              padding: 12px 16px;
              background: rgba(16, 185, 129, 0.15);
              border-radius: 12px;
              border: 1px solid rgba(16, 185, 129, 0.3);
              display: none;
              font-weight: 500;
            }
            
            .mode-toggle {
              text-align: center;
              margin-bottom: 24px;
              font-size: 15px;
              color: #cbd5e1;
            }
            
            .mode-toggle button {
              background: none;
              border: none;
              color: #3b82f6;
              text-decoration: underline;
              cursor: pointer;
              font-size: 15px;
              font-weight: 600;
              transition: color 0.3s ease;
            }
            
            .mode-toggle button:hover {
              color: #2563eb;
            }
            
            .password-input {
              position: relative;
            }
            
            .toggle-password {
              position: absolute;
              right: 16px;
              top: 50%;
              transform: translateY(-50%);
              background: none;
              border: none;
              color: #94a3b8;
              cursor: pointer;
              font-size: 14px;
              padding: 4px;
            }
            
            .toggle-password:hover {
              color: #e2e8f0;
            }
          </style>
        </head>
        <body>
          <div class="auth-container">
            <div class="auth-card">
              <div class="mode-toggle">
                <span id="mode-text">Нет аккаунта? </span>
                <button id="toggle-mode">Зарегистрироваться</button>
              </div>
              <h2 id="form-title" style="color: white;">Вход</h2>
              <form id="auth-form">
                <div class="form-group">
                  <label for="username">Логин</label>
                  <input id="username" class="auth-input" type="text" required placeholder="Введите логин" />
                </div>
                <div class="form-group">
                  <label for="password">Пароль</label>
                  <div class="password-input">
                    <input id="password" class="auth-input" type="password" required placeholder="Введите пароль" />
                    <button type="button" class="toggle-password" id="toggle-password">👁️</button>
                  </div>
                </div>
                <div class="form-group" id="balance-group" style="display: none;">
                  <label for="balance">Начальный баланс</label>
                  <input id="balance" class="auth-input" type="number" min="1" step="1" value="100" placeholder="100" />
                </div>
                <button id="submit-btn" class="auth-button" type="submit">Войти</button>
                <div id="error" class="error"></div>
                <div id="success" class="success"></div>
              </form>
            </div>
          </div>
          
          <script>
            const form = document.getElementById('auth-form');
            const errorEl = document.getElementById('error');
            const successEl = document.getElementById('success');
            const submitBtn = document.getElementById('submit-btn');
            const toggleBtn = document.getElementById('toggle-mode');
            const modeText = document.getElementById('mode-text');
            const formTitle = document.getElementById('form-title');
            const balanceGroup = document.getElementById('balance-group');
            const usernameInput = document.getElementById('username');
            const passwordInput = document.getElementById('password');
            const balanceInput = document.getElementById('balance');
            const togglePasswordBtn = document.getElementById('toggle-password');
            
            let isLogin = true; // Start with login screen
            
            // Initialize login screen
            function switchToLogin() {
              isLogin = true;
              formTitle.textContent = 'Вход';
              submitBtn.textContent = 'Войти';
              modeText.innerHTML = 'Нет аккаунта? <button id="toggle-mode">Зарегистрироваться</button>';
              balanceGroup.style.display = 'none';
              passwordInput.placeholder = 'Введите пароль';
              usernameInput.placeholder = 'Введите логин';
              errorEl.style.display = 'none';
            }
            
            function switchToRegister() {
              isLogin = false;
              formTitle.textContent = 'Регистрация';
              submitBtn.textContent = 'Зарегистрироваться';
              modeText.innerHTML = 'Уже есть аккаунт? <button id="toggle-mode">Войти</button>';
              balanceGroup.style.display = 'block';
              passwordInput.placeholder = 'Введите пароль (минимум 4 символа)';
              usernameInput.placeholder = 'Введите логин';
              errorEl.style.display = 'none';
            }
            
            // Initialize with login screen
            switchToLogin();
            
            // Toggle password visibility
            togglePasswordBtn.addEventListener('click', () => {
              const type = passwordInput.type === 'password' ? 'text' : 'password';
              passwordInput.type = type;
              togglePasswordBtn.textContent = type === 'password' ? '👁️' : '👁️‍🗨️';
            });
            
            // Toggle between login and register
            toggleBtn.addEventListener('click', () => {
              if (isLogin) {
                switchToRegister();
              } else {
                switchToLogin();
              }
            });
            
            form.addEventListener('submit', async (e) => {
              e.preventDefault();
              errorEl.style.display = 'none';
              successEl.style.display = 'none';
              
              const username = usernameInput.value.trim();
              const password = passwordInput.value.trim();
              const balanceRaw = balanceInput.value;
              const initial_balance = parseFloat(balanceRaw || '100') || 100;
              
              if (!username) {
                errorEl.textContent = 'Имя пользователя обязательно';
                errorEl.style.display = 'block';
                return;
              }
              
              if (!password) {
                errorEl.textContent = 'Пароль обязателен';
                errorEl.style.display = 'block';
                return;
              }
              
              if (!isLogin && password.length < 4) {
                errorEl.textContent = 'Пароль должен содержать минимум 4 символа';
                errorEl.style.display = 'block';
                return;
              }
              
              submitBtn.disabled = true;
              submitBtn.textContent = isLogin ? 'Вход...' : 'Регистрация...';
              
              const endpoint = isLogin ? '/login' : '/register';
              const body = JSON.stringify({
                username: username,
                password: password,
                initial_balance: initial_balance
              });
              
              console.log('Password length:', password.length);
              console.log('Initial balance:', initial_balance);
              console.log('Request body:', body);
              
              const resp = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: body
              });
              
              console.log('Response status:', resp.status);
              console.log('Response ok:', resp.ok);
              
              const responseText = await resp.text();
              console.log('Response text:', responseText);
              
              let data;
              try {
                data = JSON.parse(responseText);
              } catch (e) {
                console.log('Failed to parse JSON:', e);
                data = {};
              }

              if (!resp.ok) {
                let errorMessage = data.detail || (isLogin ? 'Ошибка входа' : 'Ошибка регистрации');
                
                // Special handling for login errors
                if (isLogin && data.detail === 'User not found') {
                  errorMessage = 'Пройдите регистрацию';
                  // Auto-switch to registration after 2 seconds
                  setTimeout(() => {
                    switchToRegister();
                  }, 2000);
                } else if (isLogin && data.detail === 'Invalid password') {
                  errorMessage = 'Неверный пароль';
                } else if (!isLogin && data.detail === 'Username already taken') {
                  errorMessage = 'Пользователь с таким логином уже существует';
                }
                
                errorEl.textContent = errorMessage;
                errorEl.style.display = 'block';
                submitBtn.disabled = false;
                submitBtn.textContent = isLogin ? 'Войти' : 'Зарегистрироваться';
                return;
              }
              
              successEl.textContent = isLogin ? 'Вход выполнен успешно!' : 'Регистрация прошла успешно!';
              successEl.style.display = 'block';
              
              // Redirect to slot game after 1.5 seconds
              setTimeout(() => {
                window.location.href = '/app?' + new URLSearchParams({
                  user_id: data.user_id,
                  username: data.username
                });
              }, 1500);
              
            });
          </script>
        </body>
        </html>
        """
    )

class HealthResponse(BaseModel):
    status: str


class SpinRequest(BaseModel):
    user_id: int
    bet: float
    client_seed: str | None = None


class SpinResponse(BaseModel):
    symbols: List[str]
    win: float
    balance: float
    spin_id: int
    server_seed_hash: str
    client_seed: str
    nonce: int
    server_seed: str | None = None


class RegisterRequest(BaseModel):
    username: str
    password: str
    initial_balance: float = 100.0


class RegisterResponse(BaseModel):
    user_id: int
    username: str
    balance: float


class LoginRequest(BaseModel):
    username: str
    password: str


class PFRotationResponse(BaseModel):
    old_server_seed: str
    old_server_seed_hash: str
    old_max_nonce: int
    new_server_seed_hash: str


def process_spin(
    user_id: int, bet: float, db: Session, client_seed: str | None = None
) -> SpinResponse:
    redis_client = get_redis()
    locked = acquire_spin_lock(redis_client, user_id)
    if not locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Spin already in progress",
        )

    try:
        client_seed = client_seed or "default-client-seed"

        if bet <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bet must be positive",
            )

        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            user = User(
                id=user_id,
                username=f"user_{user_id}",
                balance=1000.0,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        pf_state = (
            db.query(ProvablyFairState)
            .filter(ProvablyFairState.user_id == user.id)
            .first()
        )
        if pf_state is None:
            server_seed = os.urandom(32).hex()
            server_seed_hash = hashlib.sha256(
                server_seed.encode("utf-8")
            ).hexdigest()
            pf_state = ProvablyFairState(
                user_id=user.id,
                server_seed=server_seed,
                server_seed_hash=server_seed_hash,
                nonce=0,
            )
            db.add(pf_state)

        if user.balance < bet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance",
            )

        user.balance -= bet

        reels_matrix = get_reels_matrix_for_bet(db, bet, redis_client)
        current_nonce = pf_state.nonce or 0
        symbols = provably_fair_spin_reels(
            reels_matrix, pf_state.server_seed, client_seed, current_nonce
        )
        win = calculate_win(symbols, bet)
        user.balance += win

        pf_state.nonce = current_nonce + 1

        spin_record = Spin(
            user_id=user.id,
            bet=bet,
            win=win,
            symbols=json.dumps(symbols),
            pf_data={
                "server_seed_hash": pf_state.server_seed_hash,
                "server_seed": pf_state.server_seed,
                "client_seed": client_seed,
                "nonce": current_nonce,
            },
        )
        db.add(spin_record)

        session_data = (
            db.query(SessionData).filter(SessionData.user_id == user.id).first()
        )
        if session_data is None:
            session_data = SessionData(
                user_id=user.id,
                spin_count=0,
                loss_streak=0,
                current_rtp=0.0,
                total_bets=0.0,
                total_wins=0.0,
            )
            db.add(session_data)

        session_data.spin_count += 1
        session_data.total_bets += bet
        session_data.total_wins += win

        if session_data.total_bets > 0:
            session_data.current_rtp = session_data.total_wins / session_data.total_bets
        else:
            session_data.current_rtp = 0.0

        if win <= 0:
            session_data.loss_streak += 1
        else:
            session_data.loss_streak = 0

        db.commit()
        db.refresh(user)
        db.refresh(spin_record)
        db.refresh(session_data)

        event = {
            "type": "spin_performed",
            "user_id": user.id,
            "bet": bet,
            "win": win,
            "symbols": symbols,
            "balance_after": user.balance,
            "spin_id": spin_record.id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "pf": {
                "server_seed_hash": pf_state.server_seed_hash,
                "client_seed": client_seed,
                "nonce": current_nonce,
            },
        }
        publish_spin_event(event)

        return SpinResponse(
            symbols=symbols,
            win=win,
            balance=user.balance,
            spin_id=spin_record.id,
            server_seed_hash=pf_state.server_seed_hash,
            client_seed=client_seed,
            nonce=current_nonce,
            server_seed=pf_state.server_seed,
        )
    finally:
        release_spin_lock(redis_client, user_id)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/register", response_model=RegisterResponse)
def register_user(request: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    print(f"Registration request: {request}")
    username = request.username.strip()
    password = request.password
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is required",
        )
    
    if not password or len(password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 4 characters",
        )

    existing = db.query(User).filter(User.username == username).first()
    if existing is not None:
        print(f"Username '{username}' already taken")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    hashed_password = hash_password(password)
    user = User(username=username, password=hashed_password, balance=request.initial_balance)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"User created: {user.id}, {user.username}, balance: {user.balance}")

    return RegisterResponse(user_id=user.id, username=user.username, balance=user.balance)


@app.post("/login", response_model=RegisterResponse)
def login_user(request: LoginRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    username = request.username.strip()
    password = request.password
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is required",
        )
    
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required",
        )

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )
    
    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password",
        )

    return RegisterResponse(user_id=user.id, username=user.username, balance=user.balance)


@app.post("/spin", response_model=SpinResponse)
def spin_slot(request: SpinRequest, db: Session = Depends(get_db)) -> SpinResponse:
    return process_spin(request.user_id, request.bet, db, request.client_seed)


@app.post("/pf/rotate/{user_id}", response_model=PFRotationResponse)
def rotate_server_seed(user_id: int, db: Session = Depends(get_db)) -> PFRotationResponse:
    pf_state = (
        db.query(ProvablyFairState)
        .filter(ProvablyFairState.user_id == user_id)
        .first()
    )
    if pf_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provably fair state not found for user",
        )

    old_seed = pf_state.server_seed
    old_hash = pf_state.server_seed_hash
    old_max_nonce = (pf_state.nonce or 0) - 1
    if old_max_nonce < 0:
        old_max_nonce = 0

    new_seed = os.urandom(32).hex()
    new_hash = hashlib.sha256(new_seed.encode("utf-8")).hexdigest()

    pf_state.server_seed = new_seed
    pf_state.server_seed_hash = new_hash
    pf_state.nonce = 0

    db.commit()
    db.refresh(pf_state)

    return PFRotationResponse(
        old_server_seed=old_seed,
        old_server_seed_hash=old_hash,
        old_max_nonce=old_max_nonce,
        new_server_seed_hash=new_hash,
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            try:
                message = await websocket.receive_json()
            except ValueError:
                await websocket.send_json({"type": "error", "detail": "Invalid JSON"})
                continue

            action = message.get("action")
            if action != "spin":
                await websocket.send_json(
                    {"type": "error", "detail": "Unsupported action"}
                )
                continue

            user_id = int(message.get("user_id", 1))
            bet = float(message.get("bet", 0))

            db = SessionLocal()
            try:
                client_seed = message.get("client_seed")
                result = process_spin(user_id, bet, db, client_seed)
                await websocket.send_json(
                    {"type": "spin_result", "payload": result.dict()}
                )
            except HTTPException as exc:
                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": exc.detail,
                        "status_code": exc.status_code,
                    }
                )
            finally:
                db.close()
    except WebSocketDisconnect:
        return
