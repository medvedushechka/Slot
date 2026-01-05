const { useState, useEffect, useRef } = React;

// Animation utilities
const SYMBOLS = [
    { name: "cherry", image: "icons/cherry.png", weight: 30, payout: 2 },
    { name: "lemon", image: "icons/lemon.png", weight: 25, payout: 3 },
    { name: "orange", image: "icons/orange.png", weight: 25, payout: 3 },
    { name: "melon", image: "icons/melon.png", weight: 15, payout: 5 },
    { name: "kolokol", image: "icons/kolokol.png", weight: 15, payout: 5 },
    { name: "seven", image: "icons/seven.png", weight: 5, payout: 10 }
];

// Paytable: {symbol_count: multiplier}
const PAYTABLE = {
    // 3 symbols
    'cherry_3': 5,
    'kolokol_3': 8,
    'lemon_3': 3,
    'melon_3': 4,
    'orange_3': 6,
    'seven_3': 10,
    // 4 symbols  
    'cherry_4': 15,
    'kolokol_4': 25,
    'lemon_4': 10,
    'melon_4': 12,
    'orange_4': 18,
    'seven_4': 30,
    // 5 symbols
    'cherry_5': 50,
    'kolokol_5': 80,
    'lemon_5': 30,
    'melon_5': 40,
    'orange_5': 60,
    'seven_5': 100
};

// Standard slot machine paylines (including diagonals)
const STANDARD_LINES = [
    // Horizontal lines
    [
        [0, 0],
        [0, 1],
        [0, 2],
        [0, 3],
        [0, 4]
    ], // Top row
    [
        [1, 0],
        [1, 1],
        [1, 2],
        [1, 3],
        [1, 4]
    ], // Middle row
    [
        [2, 0],
        [2, 1],
        [2, 2],
        [2, 3],
        [2, 4]
    ], // Bottom row

    // Diagonal lines
    [
        [0, 0],
        [1, 1],
        [2, 2],
        [1, 3],
        [0, 4]
    ], // V-shape diagonal
    [
        [2, 0],
        [1, 1],
        [0, 2],
        [1, 3],
        [2, 4]
    ], // ^-shape diagonal

    // Additional diagonal patterns
    [
        [0, 0],
        [1, 1],
        [2, 2]
    ], // Top-left to bottom-right (3 symbols)
    [
        [2, 0],
        [1, 1],
        [0, 2]
    ], // Bottom-left to top-right (3 symbols)
    [
        [1, 0],
        [2, 1],
        [1, 2],
        [0, 3],
        [1, 4]
    ], // Diamond pattern 1
    [
        [1, 0],
        [0, 1],
        [1, 2],
        [2, 3],
        [1, 4]
    ], // Diamond pattern 2
];

// Sound management
const SoundManager = {
    backgroundMusic: null,
    rollingSound: null,
    winSound: null,
    loseSound: null,
    originalBackgroundVolume: 0.45, // Increased from 0.3 to 0.45 (1.5x louder)
    isInitialized: false,

    init() {
        this.backgroundMusic = document.getElementById('backgroundMusic');
        this.rollingSound = document.getElementById('rollingSound');
        this.winSound = document.getElementById('winSound');
        this.loseSound = document.getElementById('loseSound');

        if (!this.backgroundMusic || !this.rollingSound || !this.winSound || !this.loseSound) {
            console.log('Audio elements not found');
            return;
        }

        // Set initial volumes
        this.backgroundMusic.volume = 0;
        this.rollingSound.volume = 0.5;
        this.winSound.volume = 0.7;
        this.loseSound.volume = 0.7;

        this.isInitialized = true;

        // Try to start background music on first user interaction
        this.setupUserInteractionListener();
    },

    setupUserInteractionListener() {
        // Start background music on first user interaction (required by browsers)
        const startMusic = () => {
            if (!this.backgroundMusic.paused) return; // Already playing

            this.backgroundMusic.play().then(() => {
                console.log('Background music started');
                this.fadeInBackgroundMusic();
            }).catch(e => {
                console.log('Background music play failed:', e);
            });

            // Remove listener after first interaction
            document.removeEventListener('click', startMusic);
            document.removeEventListener('keydown', startMusic);
            document.removeEventListener('touchstart', startMusic);
        };

        // Add listeners for user interaction
        document.addEventListener('click', startMusic, { once: true });
        document.addEventListener('keydown', startMusic, { once: true });
        document.addEventListener('touchstart', startMusic, { once: true });
    },

    fadeInBackgroundMusic() {
        if (!this.backgroundMusic) return;

        // Fade in effect
        let volume = 0;
        const fadeIn = setInterval(() => {
            volume += 0.01;
            if (volume >= this.originalBackgroundVolume) {
                volume = this.originalBackgroundVolume;
                clearInterval(fadeIn);
            }
            this.backgroundMusic.volume = volume;
        }, 50);
    },

    startBackgroundMusic() {
        if (!this.isInitialized) return;

        if (this.backgroundMusic) {
            this.backgroundMusic.play().catch(e => {
                console.log('Background music play failed:', e);
                // Try again on user interaction
                this.setupUserInteractionListener();
            });
        }
    },

    startRolling() {
        if (!this.isInitialized) return;

        if (this.rollingSound) {
            this.rollingSound.currentTime = 0;
            this.rollingSound.play().catch(e => console.log('Rolling sound play failed:', e));
        }
        // Reduce background volume
        if (this.backgroundMusic) {
            this.backgroundMusic.volume = this.originalBackgroundVolume / 2.5;
        }
    },

    stopRolling() {
        if (!this.isInitialized) return;

        if (this.rollingSound) {
            this.rollingSound.pause();
            this.rollingSound.currentTime = 0;
        }
        // Restore background volume
        if (this.backgroundMusic) {
            this.backgroundMusic.volume = this.originalBackgroundVolume;
        }
    },

    playWinSound() {
        if (!this.isInitialized) return;

        if (this.winSound) {
            this.winSound.currentTime = 0;
            this.winSound.play().catch(e => console.log('Win sound play failed:', e));
        }
    },

    playLoseSound() {
        if (!this.isInitialized) return;

        if (this.loseSound) {
            this.loseSound.currentTime = 0;
            this.loseSound.play().catch(e => console.log('Lose sound play failed:', e));
        }
    }
};

// Active lines (all lines including diagonals)
const ACTIVE_LINES = STANDARD_LINES;

// Canvas drawing functions for win line
function drawWinningLines(allWinningLines) {
    const canvas = document.getElementById('win-line-canvas');
    if (!canvas || !allWinningLines || allWinningLines.length === 0) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Get slot dimensions
    const slotWidth = canvas.width / 5; // 5 columns
    const slotHeight = canvas.height / 3; // 3 rows

    // Draw each winning line
    allWinningLines.forEach((winningSlots, lineIndex) => {
        if (winningSlots.length < 2) return;

        // Get center coordinates of each slot
        const points = winningSlots.map(slot => {
            return {
                x: getSlotCenterX(slot.col, slotWidth),
                y: getSlotCenterY(slot.row, slotHeight)
            };
        });

        // Sort by columns left to right
        points.sort((a, b) => {
            const slotA = winningSlots.find(s =>
                getSlotCenterX(s.col, slotWidth) === a.x &&
                getSlotCenterY(s.row, slotHeight) === a.y
            );
            const slotB = winningSlots.find(s =>
                getSlotCenterX(s.col, slotWidth) === b.x &&
                getSlotCenterY(s.row, slotHeight) === b.y
            );
            return slotA.col - slotB.col;
        });

        // Determine line type
        const first = winningSlots[0];
        const last = winningSlots[winningSlots.length - 1];

        let isDiagonal = false;
        let isVertical = false;

        // Check diagonal (row change equals column change)
        if (Math.abs(last.row - first.row) === Math.abs(last.col - first.col)) {
            isDiagonal = true;
        }
        // Check vertical (all columns same)
        else if (winningSlots.every(slot => slot.col === first.col)) {
            isVertical = true;
        }

        // Draw line with different colors for different lines
        ctx.beginPath();

        // Different colors for different winning lines
        const colors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'];
        ctx.strokeStyle = colors[lineIndex % colors.length];
        ctx.lineWidth = 3;
        ctx.shadowColor = colors[lineIndex % colors.length] + 'cc';
        ctx.shadowBlur = 10;

        if (isDiagonal) {
            // For diagonal, draw straight line from first to last
            ctx.moveTo(points[0].x, points[0].y);
            ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
        } else if (isVertical) {
            // For vertical, connect all points
            ctx.moveTo(points[0].x, points[0].y);
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo(points[i].x, points[i].y);
            }
        } else {
            // For horizontal or broken line
            ctx.moveTo(points[0].x, points[0].y);
            for (let i = 1; i < points.length; i++) {
                ctx.lineTo(points[i].x, points[i].y);
            }
        }

        ctx.stroke();
    });
}

// Keep old function for compatibility
function drawWinningLine(winningSlots) {
    drawWinningLines([winningSlots]);
}

function getSlotCenterX(col, slotWidth) {
    return col * slotWidth + slotWidth / 2;
}

function getSlotCenterY(row, slotHeight) {
    return row * slotHeight + slotHeight / 2;
}

// Check win on a single line
function checkLineWin(lineSymbols) {
    if (!lineSymbols || lineSymbols.length === 0) return null;

    const firstSymbol = lineSymbols[0];
    let count = 1; // First symbol already matched

    for (let i = 1; i < lineSymbols.length; i++) {
        if (lineSymbols[i].name === firstSymbol.name) {
            count++;
        } else {
            break; // Stop at first different symbol
        }
    }

    // Need at least 3 matching symbols for a win
    if (count >= 3) {
        const key = `${firstSymbol.name}_${count}`;
        return {
            symbol: firstSymbol,
            count: count,
            payout: PAYTABLE[key] || 0
        };
    }

    return null;
}

// Check all active lines
function checkAllLines(reels, activeLines) {
    const wins = [];

    for (let i = 0; i < activeLines.length; i++) {
        const line = activeLines[i];
        const lineSymbols = [];

        // Get symbols for this line
        for (let j = 0; j < line.length; j++) {
            const [row, col] = line[j];
            if (reels[col] && reels[col][row]) {
                lineSymbols.push(reels[col][row]);
            }
        }

        // Check if this line has a win
        if (lineSymbols.length > 0) {
            const win = checkLineWin(lineSymbols);
            if (win) {
                wins.push({
                    lineIndex: i,
                    line: line,
                    ...win
                });
            }
        }
    }

    return wins;
}

// Calculate total win
function calculateTotalWin(reels, betPerLine) {
    const wins = checkAllLines(reels, ACTIVE_LINES);
    let totalWin = 0;
    const winDetails = [];

    for (const win of wins) {
        const lineWin = betPerLine * win.multiplier;
        totalWin += lineWin;

        winDetails.push({
            line: win.line,
            symbol: win.symbol,
            count: win.count,
            multiplier: win.multiplier,
            win: lineWin
        });
    }

    return {
        totalWin: totalWin,
        wins: winDetails
    };
}

const FIXED_BETS = [0.20, 0.40, 0.60, 0.80, 1.00, 1.20, 1.40, 1.60, 1.80, 2.00];

// Weighted random selection
function getRandomSymbol() {
    const totalWeight = SYMBOLS.reduce((sum, symbol) => sum + symbol.weight, 0);
    let random = Math.random() * totalWeight;

    for (const symbol of SYMBOLS) {
        random -= symbol.weight;
        if (random <= 0) {
            return symbol;
        }
    }
    return SYMBOLS[0];
}

function useThreeBackground(containerRef) {
    useEffect(() => {
        if (!containerRef.current || !window.THREE) return;

        const width = containerRef.current.clientWidth;
        const height = containerRef.current.clientHeight || 200;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        camera.position.z = 8;

        const renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true,
        });
        renderer.setSize(width, height);
        renderer.setPixelRatio(window.devicePixelRatio || 1);
        containerRef.current.appendChild(renderer.domElement);

        // Create more animated cubes for 5 reels
        const geometry = new THREE.BoxGeometry(1.0, 1.0, 1.0);
        const colors = [0x22c55e, 0x3b82f6, 0xf97316, 0xa855f7, 0xfbbf24];
        const cubes = colors.map((c, i) => {
            const material = new THREE.MeshStandardMaterial({
                color: c,
                metalness: 0.7,
                roughness: 0.2,
                emissive: c,
                emissiveIntensity: 0.1,
            });
            const cube = new THREE.Mesh(geometry, material);
            cube.position.x = (i - 2) * 2.0;
            cube.position.y = Math.sin(i) * 0.5;
            scene.add(cube);
            return cube;
        });

        // Enhanced lighting
        const light1 = new THREE.PointLight(0xffffff, 1.5, 30);
        light1.position.set(0, 6, 8);
        scene.add(light1);

        const light2 = new THREE.PointLight(0x22c55e, 1.2, 25);
        light2.position.set(-4, -2, 6);
        scene.add(light2);

        const light3 = new THREE.PointLight(0x3b82f6, 1.2, 25);
        light3.position.set(4, -2, 6);
        scene.add(light3);

        let frameId;

        const animate = () => {
            frameId = requestAnimationFrame(animate);
            cubes.forEach((cube, idx) => {
                const speed = 0.008 + idx * 0.003;
                cube.rotation.x += speed;
                cube.rotation.y += speed * 1.2;
                cube.position.y = Math.sin(Date.now() * 0.001 + idx) * 0.3;
            });
            renderer.render(scene, camera);
        };

        animate();

        const handleResize = () => {
            if (!containerRef.current) return;
            const newWidth = containerRef.current.clientWidth;
            const newHeight = containerRef.current.clientHeight || height;
            renderer.setSize(newWidth, newHeight);
            camera.aspect = newWidth / newHeight;
            camera.updateProjectionMatrix();
        };

        window.addEventListener("resize", handleResize);

        return () => {
            cancelAnimationFrame(frameId);
            window.removeEventListener("resize", handleResize);
            if (
                renderer.domElement &&
                renderer.domElement.parentNode === containerRef.current
            ) {
                containerRef.current.removeChild(renderer.domElement);
            }
            renderer.dispose();
        };
    }, [containerRef]);
}

// Custom hook for smooth slot machine spinning animation
function useSpinningAnimation(duration = 3000) {
    const [isSpinning, setIsSpinning] = useState(false);
    const [spinningSymbols, setSpinningSymbols] = useState([]);
    const [spinningStates, setSpinningStates] = useState([false, false, false, false, false]);
    const [reelPositions, setReelPositions] = useState([0, 0, 0, 0, 0]);

    const startSpinning = (finalSymbols) => {
        setIsSpinning(true);
        setSpinningStates([true, true, true, true, true]);
        setReelPositions([0, 0, 0, 0, 0]);

        // Start rolling sound
        SoundManager.startRolling();

        // Create symbol arrays for each reel with final symbols already in place
        const reelSymbols = [];
        for (let col = 0; col < 5; col++) {
            const symbols = [];
            // Create 30 symbols for very smooth scrolling
            for (let i = 0; i < 30; i++) {
                if (i >= 15 && i <= 17) {
                    // Final symbols in the middle - these will be visible when stopped
                    symbols[i] = finalSymbols[col][i - 15];
                } else {
                    // Random symbols for scrolling
                    symbols[i] = getRandomSymbol();
                }
            }
            reelSymbols.push(symbols);
        }
        setSpinningSymbols(reelSymbols);

        // Animation parameters
        const symbolHeight = 93.33;
        const pixelsPerSecond = 800; // Speed of scrolling

        // Start time
        const startTime = Date.now();

        // Reel stop times
        const reelStopTimes = [
            duration, // Reel 1
            duration + 200, // Reel 2  
            duration + 400, // Reel 3
            duration + 600, // Reel 4
            duration + 800 // Reel 5
        ];

        // Simple smooth animation loop
        const animateReels = () => {
            const currentTime = Date.now();
            const elapsed = currentTime - startTime;

            const newPositions = reelSymbols.map((symbols, reelIndex) => {
                const stopTime = reelStopTimes[reelIndex];

                if (elapsed < stopTime) {
                    // Simple linear scrolling
                    const scrollDistance = (elapsed * pixelsPerSecond) / 1000;
                    const maxScroll = 30 * symbolHeight;
                    const position = -(scrollDistance % maxScroll);

                    return position;
                } else {
                    // Stopped - show final symbols
                    return -15 * symbolHeight;
                }
            });

            setReelPositions(newPositions);

            // Update spinning states
            const newSpinningStates = newPositions.map((position, index) => {
                return elapsed < reelStopTimes[index];
            });
            setSpinningStates(newSpinningStates);

            // Continue animation
            if (elapsed < reelStopTimes[4] + 500) {
                requestAnimationFrame(animateReels);
            } else {
                // Animation complete - stop rolling sound
                SoundManager.stopRolling();
                setIsSpinning(false);
                setSpinningStates([false, false, false, false, false]);
                // Keep spinningSymbols and reelPositions as-is to show final symbols
            }
        };

        // Start animation
        requestAnimationFrame(animateReels);
    };

    return { isSpinning, spinningSymbols, spinningStates, reelPositions, startSpinning };
}

// Symbol Component with images
function Symbol({ symbol, isSpinning, isReelSpinning }) {
    if (isReelSpinning) {
        // Show random symbol when this specific reel is spinning
        return React.createElement("img", {
            src: symbol.image,
            alt: symbol.name,
            className: "symbol-image spinning",
            style: {
                width: "80%",
                height: "80%",
                objectFit: "contain"
            }
        });
    }

    return React.createElement("img", {
        src: symbol.image,
        alt: symbol.name,
        className: "symbol-image",
        style: {
            width: "80%",
            height: "80%",
            objectFit: "contain"
        }
    });
}

// Main Slot Game Component
function SlotGame({ username, balance, onLogout, onSpin, isSpinning, symbols, bet, setBet, lastWin, totalWins, totalSpins, spinningSymbols, spinningStates, winLineRow, winSymbolCount, winningPositions, allWinningLines, lineType, showBetDropdown, setShowBetDropdown, handleBetSelect, reelPositions }) {
    // Draw win line when winning positions change
    React.useEffect(() => {
        if (!isSpinning && allWinningLines.length > 0) {
            // Draw all winning lines
            drawWinningLines(allWinningLines);
        } else {
            // Clear canvas when no win or spinning
            const canvas = document.getElementById('win-line-canvas');
            if (canvas) {
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }
        }
    }, [allWinningLines, isSpinning]);
    return React.createElement("div", { className: "slot-game" },
        // Header with balance and logout
        React.createElement("div", { className: "game-header" },
            React.createElement("div", { className: "user-info" },
                React.createElement("span", { className: "username" }, username),
                React.createElement("button", { onClick: onLogout, className: "logout-button" }, "Выйти")
            ),
            React.createElement("div", { className: "balance-display" },
                React.createElement("div", { className: "balance-amount" }, `${balance.toFixed(2)} ₽`),
                React.createElement("div", { className: "balance-label" }, "Баланс")
            )
        ),

        // Slot machine reels
        React.createElement("div", { className: "slot-machine" },
            React.createElement("div", { ref: useRef(null), className: "three-container" }),
            React.createElement("div", { className: "reels-container" },
                // Win line canvas for dynamic drawing
                React.createElement("canvas", {
                    id: "win-line-canvas",
                    className: "win-line-canvas",
                    width: 500,
                    height: 300
                }),
                // Create 5 columns, each with 3 rows
                Array.from({ length: 5 }).map((_, colIndex) =>
                    React.createElement("div", {
                            key: colIndex,
                            className: `reel reel-column ${spinningStates && spinningStates[colIndex] ? 'spinning' : ''}`
                        },
                        // Inner reel container for scrolling animation
                        React.createElement("div", {
                                className: "reel-inner",
                                style: {
                                    transform: `translateY(${reelPositions ? reelPositions[colIndex] || 0 : 0}px)`
                                }
                            },
                            // Always use spinningSymbols array (contains final symbols in correct positions)
                            (spinningSymbols && spinningSymbols[colIndex] ?
                                spinningSymbols[colIndex] : [
                                    ...Array(15).fill(null).map(() => getRandomSymbol()),
                                    ...(symbols[colIndex] || [getRandomSymbol(), getRandomSymbol(), getRandomSymbol()]),
                                    ...Array(12).fill(null).map(() => getRandomSymbol())
                                ]
                            ).map((symbol, symbolIndex) => {
                                // Check if this is a winning position (only for visible symbols 15,16,17)
                                const isVisibleSymbol = symbolIndex >= 15 && symbolIndex <= 17;
                                const rowIndex = symbolIndex - 15; // Convert to 0,1,2 for row positions

                                // Check if this position matches any winning position
                                const isWinningPosition = winningPositions.some(([winRow, winCol]) =>
                                    winRow === rowIndex && winCol === colIndex
                                );

                                return React.createElement("div", {
                                        key: symbolIndex,
                                        className: `symbol ${isWinningPosition && !isSpinning && isVisibleSymbol ? 'winning' : ''}`
                                    },
                                    React.createElement("img", {
                                        src: symbol.image,
                                        alt: symbol.name,
                                        className: "symbol-image"
                                    })
                                );
                            })
                        )
                    )
                )
            ),

            // Controls container with explicit order
            React.createElement("div", { className: "controls-container" },
                // Spin button
                React.createElement("button", {
                    onClick: onSpin,
                    disabled: isSpinning || balance < bet,
                    className: `spin-button ${isSpinning ? 'spinning' : ''} ${balance < bet ? 'disabled' : ''}`
                }, isSpinning ? "КРУТИТСЯ..." : "КРУТИТЬ"),

                // Bet button with modal dropdown
                React.createElement("div", { className: "bet-button-container" },
                    React.createElement("button", {
                        onClick: () => setShowBetDropdown(!showBetDropdown),
                        className: "bet-dropdown-button"
                    }, `Ставка: ${bet.toFixed(2)} ₽`),

                    // Modal overlay
                    showBetDropdown && React.createElement("div", {
                            className: "bet-dropdown-overlay",
                            onClick: () => setShowBetDropdown(false)
                        },
                        React.createElement("div", {
                                className: "bet-dropdown-modal",
                                onClick: (e) => e.stopPropagation() // Prevent closing when clicking modal
                            },
                            React.createElement("div", { className: "bet-dropdown-header" },
                                React.createElement("h3", { className: "bet-dropdown-title" }, "Выберите ставку")
                            ),
                            React.createElement("div", { className: "bet-dropdown-content" },
                                ...FIXED_BETS.map(betAmount =>
                                    React.createElement("button", {
                                        key: betAmount,
                                        onClick: () => handleBetSelect(betAmount),
                                        className: `bet-dropdown-item ${bet === betAmount ? 'active' : ''}`
                                    }, `${betAmount.toFixed(2)} ₽`)
                                )
                            )
                        )
                    )
                )
            ),

            // Stats
            React.createElement("div", { className: "game-stats" },
                React.createElement("div", { className: "stat-item" },
                    React.createElement("div", { className: "stat-label" }, "Последний выигрыш"),
                    React.createElement("div", {
                        className: `stat-value ${lastWin && lastWin > 0 ? 'win' : ''}`
                    }, lastWin ? `${lastWin.toFixed(2)} ₽` : "-")
                ),
                React.createElement("div", { className: "stat-item" },
                    React.createElement("div", { className: "stat-label" }, "Всего вращений"),
                    React.createElement("div", { className: "stat-value" }, totalSpins)
                ),
                React.createElement("div", { className: "stat-item" },
                    React.createElement("div", { className: "stat-label" }, "Выигрышей"),
                    React.createElement("div", { className: "stat-value" }, totalWins)
                ),
                React.createElement("div", { className: "stat-item" },
                    React.createElement("div", { className: "stat-label" }, "RTP"),
                    React.createElement("div", { className: "stat-value" },
                        totalSpins > 0 ? `${((totalWins / totalSpins) * 100).toFixed(1)}%` : "0%"
                    )
                )
            )
        )
    )
}

function App() {
    // Get URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const userId = urlParams.get('user_id');
    const username = urlParams.get('username');

    // Game states
    const [balance, setBalance] = useState(100.00);
    const [bet, setBet] = useState(0.20);
    const [symbols, setSymbols] = useState([
        [getRandomSymbol(), getRandomSymbol(), getRandomSymbol()],
        [getRandomSymbol(), getRandomSymbol(), getRandomSymbol()],
        [getRandomSymbol(), getRandomSymbol(), getRandomSymbol()],
        [getRandomSymbol(), getRandomSymbol(), getRandomSymbol()],
        [getRandomSymbol(), getRandomSymbol(), getRandomSymbol()]
    ]);
    const [lastWin, setLastWin] = useState(null);
    const [totalWins, setTotalWins] = useState(0);
    const [totalSpins, setTotalSpins] = useState(0);
    const [winLineRow, setWinLineRow] = useState(null); // null, 'top', 'middle', 'bottom'
    const [winSymbolCount, setWinSymbolCount] = useState(null); // null, 3, 4, 5
    const [winningPositions, setWinningPositions] = useState([]); // Track winning symbol positions
    const [allWinningLines, setAllWinningLines] = useState([]); // Track all winning lines
    const [lineType, setLineType] = useState(null); // 'horizontal', 'diagonal-up', 'diagonal-down'
    const [showBetDropdown, setShowBetDropdown] = useState(false); // Bet dropdown visibility

    const { isSpinning, spinningSymbols, spinningStates, reelPositions, startSpinning } = useSpinningAnimation();
    const threeRef = useRef(null);

    useThreeBackground(threeRef);

    // Initialize sound manager
    React.useEffect(() => {
        SoundManager.init();
    }, []);

    const handleLogout = () => {
        window.location.href = '/';
    };

    const handleBetSelect = (newBet) => {
        setBet(newBet);
        setShowBetDropdown(false);
    };

    // Game functions
    const onSpin = () => {
        if (balance < bet) return;

        // Clear win line when starting new spin
        setWinLineRow(null);
        setWinSymbolCount(null);
        setWinningPositions([]);
        setAllWinningLines([]);
        setLineType(null);

        // Simulate spin result for 3x5 grid
        const finalSymbols = [
            [getRandomSymbol(), getRandomSymbol(), getRandomSymbol()],
            [getRandomSymbol(), getRandomSymbol(), getRandomSymbol()],
            [getRandomSymbol(), getRandomSymbol(), getRandomSymbol()],
            [getRandomSymbol(), getRandomSymbol(), getRandomSymbol()],
            [getRandomSymbol(), getRandomSymbol(), getRandomSymbol()]
        ];

        // Calculate win based on final symbols
        let winAmount = 0;
        let winningRow = null;
        let winSymbolCount = null;
        let winningPositions = [];
        let allWinningLinesData = [];
        let lineType = null; // 'horizontal' or 'diagonal-up' or 'diagonal-down'

        // Check all lines for wins
        const allLines = checkAllLines(finalSymbols, ACTIVE_LINES);
        if (allLines.length > 0) {
            // Calculate total win from all winning lines
            winAmount = allLines.reduce((total, line) => total + (line.payout * bet), 0);

            // Collect all winning positions for all lines
            allWinningLinesData = allLines.map(line => {
                const linePattern = ACTIVE_LINES[line.lineIndex];
                const matchingCount = line.count;

                // Only include positions that actually match
                const positions = linePattern.slice(0, matchingCount).map(([row, col]) => ({ row, col }));

                return positions;
            });

            // For display purposes, use the best line (highest payout)
            const bestLine = allLines[0];
            const linePattern = ACTIVE_LINES[bestLine.lineIndex];
            const matchingCount = bestLine.count;

            winningPositions = linePattern.slice(0, matchingCount).map(([row, col]) => [row, col]);

            // Determine line type and position for display
            if (linePattern.length === 5) {
                lineType = 'horizontal';
                const row = linePattern[0][0];
                if (row === 0) winningRow = 'top';
                else if (row === 1) winningRow = 'middle';
                else if (row === 2) winningRow = 'bottom';
            } else if (linePattern.length === 3) {
                const firstPos = linePattern[0];
                const lastPos = linePattern[2];

                if (firstPos[0] < lastPos[0]) {
                    lineType = 'diagonal-down';
                } else {
                    lineType = 'diagonal-up';
                }

                const middleRow = linePattern[1][0];
                if (middleRow === 0) winningRow = 'top';
                else if (middleRow === 1) winningRow = 'middle';
                else if (middleRow === 2) winningRow = 'bottom';
            }

            winSymbolCount = matchingCount;
        }

        // Start animation
        startSpinning(finalSymbols);

        // Update game state after animation
        setTimeout(() => {
            // Don't setSymbols - spinningSymbols already contains final symbols
            const newBalance = balance - bet + (winAmount || 0);
            setBalance(newBalance);
            setLastWin(winAmount || 0);
            setTotalSpins(prev => prev + 1);
            setWinLineRow(winningRow); // Set win line position
            setWinSymbolCount(winSymbolCount); // Set win line length
            setWinningPositions(winningPositions); // Set winning symbol positions
            setAllWinningLines(allWinningLinesData); // Set all winning lines for drawing
            setLineType(lineType); // Set line type for proper rendering

            // Play sound effects
            if (winAmount > 0) {
                SoundManager.playWinSound();
                setTotalWins(prev => prev + 1);
            } else {
                SoundManager.playLoseSound();
            }
        }, 4000); // Match with animation completion time
    };

    return React.createElement(SlotGame, {
        username: username || "Player",
        balance,
        onLogout: handleLogout,
        onSpin,
        isSpinning,
        symbols,
        bet,
        setBet,
        lastWin,
        totalWins,
        totalSpins,
        spinningSymbols,
        spinningStates,
        winLineRow,
        winSymbolCount,
        winningPositions,
        allWinningLines,
        lineType,
        showBetDropdown,
        setShowBetDropdown,
        handleBetSelect,
        reelPositions
    });
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(React.createElement(App));