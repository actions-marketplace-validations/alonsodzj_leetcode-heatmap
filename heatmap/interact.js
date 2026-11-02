// Efectos interactivos del heatmap.
//
// Solo se ejecuta cuando el SVG está incrustado en una página o abierto
// directamente; dentro de un <img> (README de GitHub) el navegador lo ignora.
//
// Cada celda se mueve y escala únicamente dentro de su propio hueco de la
// rejilla (cell_size + cell_gap), así que nunca puede solaparse con otra.
(() => {
  const CFG = __CONFIG__;
  const svg = document.getElementById(CFG.id);
  if (!svg) return;

  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const { size, step, gap } = CFG;
  const maxScale = step / size;
  const vb = svg.viewBox.baseVal;

  const cells = Array.from(svg.querySelectorAll('.c'), (el) => ({
    el,
    col: +el.dataset.c,
    row: +el.dataset.r,
    lvl: +el.dataset.l,
    x: +el.dataset.x,
    y: +el.dataset.y,
    ox: 0, oy: 0, k: 1, op: 1,
    vx: 0, vy: 0, vk: 0,
  }));
  const byPos = new Map(cells.map((c) => [`${c.col},${c.row}`, c]));

  let pointer = null;
  let hovered = null;
  let ripples = [];
  let frameId = 0;
  let introCleared = false;

  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

  function toLocal(e) {
    const m = svg.getScreenCTM();
    if (!m) return null;
    const p = svg.createSVGPoint();
    p.x = e.clientX;
    p.y = e.clientY;
    return p.matrixTransform(m.inverse());
  }

  function cellAt(p) {
    const col = Math.floor((p.x - CFG.x0 + gap / 2) / step);
    const row = Math.floor((p.y - CFG.y0 + gap / 2) / step);
    return byPos.get(`${col},${row}`) || null;
  }

  // Posición y escala objetivo de una celda según el puntero y las ondas.
  function target(c, now) {
    let tx = 0, ty = 0, tk = 1, op = 1;

    if (pointer) {
      const dx = pointer.x - c.x;
      const dy = pointer.y - c.y;
      const d = Math.hypot(dx, dy);
      const f = d < CFG.radius ? (1 - d / CFG.radius) ** 2 : 0;

      if (f > 0 && !reduceMotion) {
        if (CFG.effect === 'magnify') {
          tk = 1 + (maxScale - 1) * CFG.strength * f;
        } else if (CFG.effect === 'gravity' || CFG.effect === 'repel') {
          tk = 1 - CFG.shrink * f;
          const room = (step - size * tk) / 2;
          const sign = CFG.effect === 'gravity' ? 1 : -1;
          // Cerca del centro la dirección es inestable: se atenúa.
          const mag = room * CFG.strength * Math.min(1, f * 2) * Math.min(1, d / size);
          tx = (sign * dx / (d || 1)) * mag;
          ty = (sign * dy / (d || 1)) * mag;
        }
      }
      if (CFG.spotlight) {
        op = CFG.spotlightDim + (1 - CFG.spotlightDim) * clamp(1 - d / (CFG.radius * 1.8), 0, 1);
      }
    }

    if (!reduceMotion) {
      for (const r of ripples) {
        const age = (now - r.t0) / 1000;
        const front = age * CFG.rippleSpeed;
        const d = Math.hypot(c.x - r.x, c.y - r.y);
        const band = Math.exp(-(((d - front) / (step * 1.3)) ** 2));
        tk += CFG.rippleScale * band * (1 - age / r.life);
      }
    }
    return { tx, ty, tk: clamp(tk, 0.2, maxScale), op };
  }

  function frame() {
    frameId = 0;
    const now = performance.now();
    ripples = ripples.filter((r) => (now - r.t0) / 1000 < r.life);
    let moving = ripples.length > 0;

    for (const c of cells) {
      const t = target(c, now);

      // Muelle amortiguado: da la sensación de inercia.
      c.vx = (c.vx + (t.tx - c.ox) * CFG.stiffness) * CFG.damping;
      c.vy = (c.vy + (t.ty - c.oy) * CFG.stiffness) * CFG.damping;
      c.vk = (c.vk + (t.tk - c.k) * CFG.stiffness) * CFG.damping;
      c.ox += c.vx;
      c.oy += c.vy;
      c.k = clamp(c.k + c.vk, 0.2, maxScale);
      c.op += (t.op - c.op) * 0.2;

      // La celda no puede salir de su hueco: garantiza que no hay solapes.
      const room = Math.max(0, (step - size * c.k) / 2);
      if (Math.abs(c.ox) > room) { c.ox = Math.sign(c.ox) * room; c.vx = 0; }
      if (Math.abs(c.oy) > room) { c.oy = Math.sign(c.oy) * room; c.vy = 0; }

      const resting = Math.abs(c.ox) < 0.01 && Math.abs(c.oy) < 0.01 &&
                      Math.abs(c.k - 1) < 0.001 && Math.abs(c.op - 1) < 0.005;
      if (resting) {
        if (c.el.style.transform) {
          c.el.style.transform = '';
          c.el.style.opacity = '';
        }
        c.ox = c.oy = 0; c.k = 1; c.op = 1;
        c.vx = c.vy = c.vk = 0;
      } else {
        c.el.style.transform = `translate(${c.ox.toFixed(2)}px,${c.oy.toFixed(2)}px) scale(${c.k.toFixed(3)})`;
        c.el.style.opacity = c.op < 0.995 ? c.op.toFixed(3) : '';
      }

      if (Math.abs(c.vx) + Math.abs(c.vy) + Math.abs(c.vk) > 0.005 ||
          Math.abs(t.tx - c.ox) + Math.abs(t.ty - c.oy) + Math.abs(t.tk - c.k) + Math.abs(t.op - c.op) > 0.01) {
        moving = true;
      }
    }
    if (moving) schedule();
  }

  function schedule() {
    if (!frameId) frameId = requestAnimationFrame(frame);
  }

  function focus(cell) {
    if (cell === hovered) return;
    hovered = cell;
    if (!CFG.crosshair && !CFG.sameLevel) return;
    svg.classList.toggle('fx', !!cell);
    for (const c of cells) {
      const on = !!cell && (
        (CFG.crosshair && (c.col === cell.col || c.row === cell.row)) ||
        (CFG.sameLevel && c.lvl === cell.lvl));
      c.el.classList.toggle('on', on);
    }
  }

  svg.addEventListener('pointerenter', () => {
    // Las animaciones CSS fijan transform y pisarían el efecto.
    if (CFG.introAnimation && !introCleared) {
      cells.forEach((c) => c.el.classList.remove('an'));
      introCleared = true;
    }
    svg.classList.add('live');
  });

  svg.addEventListener('pointermove', (e) => {
    pointer = toLocal(e);
    const cell = pointer && cellAt(pointer);
    focus(cell);
    schedule();
  });

  svg.addEventListener('pointerleave', () => {
    pointer = null;
    focus(null);
    svg.classList.remove('live');
    schedule();
  });

  if (CFG.ripple) {
    svg.addEventListener('pointerdown', (e) => {
      const p = toLocal(e);
      if (!p) return;
      const life = Math.hypot(vb.width, vb.height) / CFG.rippleSpeed + 0.4;
      ripples.push({ x: p.x, y: p.y, t0: performance.now(), life });
      schedule();
    });
  }
})();
