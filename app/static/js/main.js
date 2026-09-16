// Main Retro App Interactions: Mobile Menu, Image Preview, Screenshot Modals, Countdown Timer

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Menu Toggle
    const menuBtn = document.getElementById('mobile-menu-btn');
    const navMenu = document.getElementById('retro-nav-menu');
    if (menuBtn && navMenu) {
        menuBtn.addEventListener('click', () => {
            navMenu.classList.toggle('is-open');
            if (window.retroAudio) {
                window.retroAudio.playClick();
            }
        });
    }

    // 2. Score Screenshot Preview
    const fileInput = document.getElementById('screenshot-input');
    const previewContainer = document.getElementById('preview-container');
    const previewImg = document.getElementById('preview-img');

    if (fileInput && previewImg) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    previewImg.src = event.target.result;
                    if (previewContainer) {
                        previewContainer.style.display = 'block';
                    }
                    if (window.retroAudio) {
                        window.retroAudio.playCoin();
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // 3. Screenshot Preview Modal (Leaderboard Inspection)
    const previewModal = document.getElementById('screenshot-modal');
    const modalImg = document.getElementById('modal-screenshot-img');
    const modalUser = document.getElementById('modal-screenshot-user');
    const modalScore = document.getElementById('modal-screenshot-score');

    document.querySelectorAll('.view-screenshot-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const src = btn.getAttribute('data-screenshot');
            const user = btn.getAttribute('data-user') || '';
            const score = btn.getAttribute('data-score') || '';

            if (modalImg) modalImg.src = src;
            if (modalUser) modalUser.textContent = user;
            if (modalScore) modalScore.textContent = score;

            if (previewModal) {
                previewModal.showModal();
                if (window.retroAudio) window.retroAudio.playClick();
            }
        });
    });

    // 4. Live Countdown Timer for Active Challenge
    const countdownElem = document.getElementById('challenge-countdown');
    if (countdownElem) {
        const endDateStr = countdownElem.getAttribute('data-end-date');
        if (endDateStr) {
            const endDate = new Date(endDateStr).getTime();
            function updateTimer() {
                const now = new Date().getTime();
                const distance = endDate - now;

                if (distance < 0) {
                    countdownElem.innerHTML = "⏳ CHALLENGE TERMINÉ !";
                    return;
                }

                const days = Math.floor(distance / (1000 * 60 * 60 * 24));
                const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((distance % (1000 * 60)) / 1000);

                let display = "";
                if (days > 0) display += `${days}J `;
                display += `${String(hours).padStart(2, '0')}H ${String(minutes).padStart(2, '0')}M ${String(seconds).padStart(2, '0')}S`;

                countdownElem.textContent = display;
            }
            updateTimer();
            setInterval(updateTimer, 1000);
        }
    }
});

// Admin Slot Machine Random Roll Helper
window.rollRandomGame = async function() {
    const rollBtn = document.getElementById('btn-roll-game');
    const resultBox = document.getElementById('random-roll-display');
    const gameSelect = document.getElementById('game-select');
    if (!rollBtn || !resultBox) return;

    rollBtn.disabled = true;
    rollBtn.classList.add('is-disabled');

    try {
        const res = await fetch('/api/games/random-pool');
        const games = await res.json();

        if (!games || games.length === 0) {
            alert("Aucun jeu dans le pool de sélection aléatoire ! Ajoutez d'abord des jeux.");
            rollBtn.disabled = false;
            rollBtn.classList.remove('is-disabled');
            return;
        }

        // Slot machine animation
        let count = 0;
        const totalTicks = 20;
        const interval = setInterval(() => {
            const randomGame = games[Math.floor(Math.random() * games.length)];
            resultBox.innerHTML = `🎲 <span class="nes-text is-warning">${randomGame.name}</span> (${randomGame.platform})`;
            if (window.retroAudio) window.retroAudio.playRollTick();
            count++;

            if (count >= totalTicks) {
                clearInterval(interval);
                // Choose final winner
                const winner = games[Math.floor(Math.random() * games.length)];
                resultBox.innerHTML = `⭐ <span class="nes-text is-success font-bold">${winner.name}</span> (${winner.platform}) ⭐`;
                if (gameSelect) {
                    gameSelect.value = winner.id;
                }
                if (window.retroAudio) window.retroAudio.playPowerup();
                rollBtn.disabled = false;
                rollBtn.classList.remove('is-disabled');
            }
        }, 100);

    } catch (err) {
        console.error("Roll failed:", err);
        rollBtn.disabled = false;
        rollBtn.classList.remove('is-disabled');
    }
};