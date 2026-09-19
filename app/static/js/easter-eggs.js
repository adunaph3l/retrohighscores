// Easter Eggs: Konami Code, CRT Mode, Pixel Confetti

// 1. CRT Scanlines Toggle
function initCrtMode() {
    const isCrt = localStorage.getItem('retro_crt_enabled') === 'true';
    if (isCrt) {
        document.body.classList.add('crt-active');
    }
    updateCrtButton();
}

function toggleCrtMode() {
    const active = document.body.classList.toggle('crt-active');
    localStorage.setItem('retro_crt_enabled', active);
    updateCrtButton();
    if (window.retroAudio) {
        window.retroAudio.playClick();
    }
    if (active) {
        fetch('/api/easter-egg/crt').catch(() => {});
    }
}

function updateCrtButton() {
    const btn = document.getElementById('retro-crt-btn');
    if (btn) {
        const active = document.body.classList.contains('crt-active');
        btn.innerHTML = active ? '📺 CRT: ON' : '📺 CRT: OFF';
        if (active) {
            btn.classList.remove('is-disabled');
            btn.classList.add('is-warning');
        } else {
            btn.classList.remove('is-warning');
            btn.classList.add('is-disabled');
        }
    }
}

// 2. Konami Code (Up Up Down Down Left Right Left Right B A)
const konamiCode = [
    'ArrowUp', 'ArrowUp',
    'ArrowDown', 'ArrowDown',
    'ArrowLeft', 'ArrowRight',
    'ArrowLeft', 'ArrowRight',
    'b', 'a'
];
let konamiPosition = 0;

document.addEventListener('keydown', (e) => {
    const requiredKey = konamiCode[konamiPosition];
    if (e.key.toLowerCase() === requiredKey.toLowerCase()) {
        konamiPosition++;
        if (konamiPosition === konamiCode.length) {
            triggerKonamiSuccess();
            konamiPosition = 0;
        }
    } else {
        konamiPosition = 0;
    }
});

function triggerKonamiSuccess() {
    if (window.retroAudio) {
        window.retroAudio.playVictory();
    }
    triggerPixelConfetti();

    // Call backend to unlock secret achievement
    fetch('/api/easter-egg/konami', { credentials: 'same-origin' })
        .then(res => res.json())
        .then(data => {
            console.log('Konami response:', data);
        })
        .catch(err => console.error(err));

    // Show retro modal dialog
    const modal = document.getElementById('konami-dialog');
    if (modal) {
        modal.showModal();
    } else {
        alert("🎮 KONAMI CODE DÉTECTÉ ! Vous avez débloqué le succès secret 'Code Konami' !");
    }
}

// 3. Pixel Confetti Animation
function triggerPixelConfetti() {
    const container = document.createElement('div');
    container.className = 'pixel-confetti-container';
    document.body.appendChild(container);

    const colors = ['#f7d51d', '#e76e55', '#92cc41', '#209cee', '#ffffff'];
    for (let i = 0; i < 50; i++) {
        const pixel = document.createElement('div');
        pixel.className = 'pixel-confetti';
        pixel.style.left = Math.random() * 100 + 'vw';
        pixel.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        pixel.style.animationDuration = (1 + Math.random() * 2) + 's';
        pixel.style.animationDelay = (Math.random() * 0.5) + 's';
        container.appendChild(pixel);
    }

    setTimeout(() => {
        container.remove();
    }, 3500);
}

document.addEventListener('DOMContentLoaded', () => {
    initCrtMode();
});