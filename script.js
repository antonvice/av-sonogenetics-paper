// Wave Animation for the interactive card
const canvasContainer = document.getElementById('waveCanvas');
const canvas = document.createElement('canvas');
canvasContainer.appendChild(canvas);
const ctx = canvas.getContext('2d');

let width, height;
let phase = 0;

function resize() {
    width = canvasContainer.offsetWidth;
    height = canvasContainer.offsetHeight;
    canvas.width = width;
    canvas.height = height;
}

window.addEventListener('resize', resize);
resize();

function draw() {
    ctx.clearRect(0, 0, width, height);

    ctx.strokeStyle = '#00d4ff';
    ctx.lineWidth = 2;
    ctx.beginPath();

    const midY = height / 2;
    const amplitude = 30;
    const frequency = 0.02;

    for (let x = 0; x < width; x++) {
        const y = midY + Math.sin(x * frequency + phase) * amplitude;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }

    ctx.stroke();

    // Add glowing effect
    ctx.shadowBlur = 15;
    ctx.shadowColor = '#00d4ff';

    phase += 0.05;
    requestAnimationFrame(draw);
}

draw();

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Interactive state tracking
console.log("Sonogenetics Paper Viewer Initialized.");
