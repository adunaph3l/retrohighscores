// Retro 8-bit Web Audio Synthesizer (Zero external audio files needed!)
class RetroAudio {
    constructor() {
        this.ctx = null;
        this.muted = localStorage.getItem('retro_audio_muted') === 'true';
        this.initOnFirstGesture();
    }

    initContext() {
        if (!this.ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                this.ctx = new AudioContext();
            }
        }
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    initOnFirstGesture() {
        const unlock = () => {
            this.initContext();
            document.removeEventListener('click', unlock);
            document.removeEventListener('keydown', unlock);
        };
        document.addEventListener('click', unlock, { once: true });
        document.addEventListener('keydown', unlock, { once: true });
    }

    toggleMute() {
        this.muted = !this.muted;
        localStorage.setItem('retro_audio_muted', this.muted);
        this.updateMuteButton();
        if (!this.muted) {
            this.playCoin();
        }
    }

    updateMuteButton() {
        const btn = document.getElementById('retro-sound-btn');
        if (btn) {
            btn.innerHTML = this.muted ? '🔇 SON: OFF' : '🔊 SON: ON';
            if (this.muted) {
                btn.classList.remove('is-success');
                btn.classList.add('is-error');
            } else {
                btn.classList.remove('is-error');
                btn.classList.add('is-success');
            }
        }
    }

    // --- Sound Effects ---

    // Retro Coin (Mario / Arcade style)
    playCoin() {
        if (this.muted) return;
        this.initContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'square';
        osc.connect(gain);
        gain.connect(this.ctx.destination);

        // Note 1: B5 (987.77 Hz)
        osc.frequency.setValueAtTime(987.77, now);
        // Note 2: E6 (1318.51 Hz)
        osc.frequency.setValueAtTime(1318.51, now + 0.08);

        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

        osc.start(now);
        osc.stop(now + 0.35);
    }

    // 8-bit Click / Blip
    playClick() {
        if (this.muted) return;
        this.initContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'triangle';
        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.04);

        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.04);

        osc.start(now);
        osc.stop(now + 0.04);
    }

    // Powerup / 1-Up Arpeggio
    playPowerup() {
        if (this.muted) return;
        this.initContext();
        if (!this.ctx) return;

        const notes = [330, 392, 659, 523, 587, 784];
        const now = this.ctx.currentTime;
        notes.forEach((freq, idx) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'square';
            osc.frequency.setValueAtTime(freq, now + idx * 0.06);
            gain.gain.setValueAtTime(0.12, now + idx * 0.06);
            gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.06 + 0.08);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now + idx * 0.06);
            osc.stop(now + idx * 0.06 + 0.08);
        });
    }

    // Game Over Descending Tone
    playGameOver() {
        if (this.muted) return;
        this.initContext();
        if (!this.ctx) return;

        const notes = [440, 415, 392, 349];
        const now = this.ctx.currentTime;
        notes.forEach((freq, idx) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(freq, now + idx * 0.15);
            gain.gain.setValueAtTime(0.15, now + idx * 0.15);
            gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.15 + 0.2);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now + idx * 0.15);
            osc.stop(now + idx * 0.15 + 0.2);
        });
    }

    // Slot Machine / Dice Roll Tick
    playRollTick() {
        if (this.muted) return;
        this.initContext();
        if (!this.ctx) return;

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'square';
        osc.frequency.setValueAtTime(550 + Math.random() * 200, now);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.05);
    }

    // Konami Code Secret Fanfare
    playVictory() {
        if (this.muted) return;
        this.initContext();
        if (!this.ctx) return;

        const melody = [
            { f: 523.25, d: 0.12 },
            { f: 659.25, d: 0.12 },
            { f: 783.99, d: 0.12 },
            { f: 1046.50, d: 0.35 }
        ];
        let offset = 0;
        const now = this.ctx.currentTime;
        melody.forEach(note => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'square';
            osc.frequency.setValueAtTime(note.f, now + offset);
            gain.gain.setValueAtTime(0.2, now + offset);
            gain.gain.exponentialRampToValueAtTime(0.001, now + offset + note.d);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now + offset);
            osc.stop(now + offset + note.d);
            offset += note.d * 0.9;
        });
    }
}

window.retroAudio = new RetroAudio();
document.addEventListener('DOMContentLoaded', () => {
    window.retroAudio.updateMuteButton();

    // Attach click sound to all retro buttons
    document.querySelectorAll('.nes-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (!btn.id || btn.id !== 'retro-sound-btn') {
                window.retroAudio.playClick();
            }
        });
    });
});