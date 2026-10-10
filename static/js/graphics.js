(() => {
  "use strict";

  const canvas = document.querySelector("#storm-canvas");
  if (!canvas) return;

  const context = canvas.getContext("2d");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let intensity = 0.35;
  let elapsed = 0;
  let lastTime = 0;

  function resizeCanvas() {
    const scale = Math.min(window.devicePixelRatio || 1, 2);
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(1, Math.floor(rect.width * scale));
    canvas.height = Math.max(1, Math.floor(rect.height * scale));
    context.setTransform(scale, 0, 0, scale, 0, 0);
  }

  function drawCloud(x, y, size) {
    context.fillStyle = "rgba(105, 128, 151, 0.78)";
    context.beginPath();
    context.arc(x, y, size * 0.32, 0, Math.PI * 2);
    context.arc(x + size * 0.28, y - size * 0.08, size * 0.42, 0, Math.PI * 2);
    context.arc(x + size * 0.62, y, size * 0.3, 0, Math.PI * 2);
    context.fill();
  }

  function drawHouse(width, height) {
    const houseWidth = Math.min(width * 0.54, 360);
    const houseHeight = Math.min(height * 0.34, 210);
    const x = width * 0.5 - houseWidth * 0.5;
    const y = height - houseHeight - 48;

    context.fillStyle = "#15273b";
    context.fillRect(x, y, houseWidth, houseHeight);

    context.fillStyle = "#0b1626";
    context.beginPath();
    context.moveTo(x - 24, y);
    context.lineTo(x + houseWidth * 0.5, y - houseHeight * 0.52);
    context.lineTo(x + houseWidth + 24, y);
    context.closePath();
    context.fill();

    const lit = intensity < 0.72;
    context.fillStyle = lit ? "#ffd67a" : "#152235";
    context.fillRect(x + houseWidth * 0.17, y + houseHeight * 0.32, 54, 48);
    context.fillRect(x + houseWidth * 0.67, y + houseHeight * 0.32, 54, 48);

    context.fillStyle = "#080f19";
    context.fillRect(x + houseWidth * 0.45, y + houseHeight * 0.45, 46, houseHeight * 0.55);
  }

  function drawRain(width, height) {
    context.strokeStyle = `rgba(164, 213, 244, ${0.25 + intensity * 0.45})`;
    context.lineWidth = 1.2;
    const drops = Math.floor(35 + intensity * 95);

    for (let index = 0; index < drops; index += 1) {
      const seed = index * 89.13;
      const x = (seed * 17 + elapsed * (45 + intensity * 80)) % (width + 80) - 40;
      const y = (seed * 31 + elapsed * (100 + intensity * 170)) % (height + 80) - 40;
      context.beginPath();
      context.moveTo(x, y);
      context.lineTo(x - 6 - intensity * 6, y + 14 + intensity * 12);
      context.stroke();
    }
  }

  function drawFrame(timestamp = 0) {
    const rect = canvas.getBoundingClientRect();
    const delta = Math.min((timestamp - lastTime) / 1000, 0.05) || 0;
    lastTime = timestamp;
    elapsed += reducedMotion ? 0 : delta;

    const sky = context.createLinearGradient(0, 0, 0, rect.height);
    sky.addColorStop(0, `rgb(${Math.round(24 - intensity * 10)}, ${Math.round(47 - intensity * 12)}, ${Math.round(75 - intensity * 15)})`);
    sky.addColorStop(1, "#13263a");
    context.fillStyle = sky;
    context.fillRect(0, 0, rect.width, rect.height);

    drawCloud(rect.width * 0.08, rect.height * 0.14, 150);
    drawCloud(rect.width * 0.56, rect.height * 0.09, 190);
    drawCloud(rect.width * 0.78, rect.height * 0.22, 125);

    context.fillStyle = "#0b1a26";
    context.fillRect(0, rect.height - 54, rect.width, 54);
    drawHouse(rect.width, rect.height);
    drawRain(rect.width, rect.height);

    if (!reducedMotion) requestAnimationFrame(drawFrame);
  }

  window.addEventListener("resize", resizeCanvas);
  window.addEventListener("fever-dreams:state", (event) => {
    const position = Number(event.detail?.current_point?.position || 1);
    intensity = Math.min(0.95, 0.25 + position * 0.085);
    if (reducedMotion) drawFrame();
  });

  resizeCanvas();
  drawFrame();
})();

