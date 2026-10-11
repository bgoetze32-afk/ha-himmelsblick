// Himmelsblick-Karte – berechnet die "Himmelsklarheit" aus Wolken in drei Höhen, Aerosolen und Strahlung.
// Wird von der Integration automatisch geladen (keine Dashboard-Ressource nötig).
(() => {
  if (customElements.get('himmelsblick-card')) return;
  const VERSION = '0.1.0';
  const SCHLUESSEL = ['wolken_gesamt', 'wolken_hoch', 'wolken_mittel', 'wolken_tief', 'aerosol', 'staub', 'feinstaub', 'strahlung', 'klarer_himmel', 'sonnenhoehe', 'verlauf'];

  // Klarheit 0–100: Anteil Himmel/Sonne, der nicht durch Schleier, Dunst oder Wolken verdeckt ist.
  // Faktoren (grobe Transmission): hohe Wolken lassen ~40 % durch, tiefe/mittlere ~10 %,
  // Aerosole nach Beer-Lambert relativ zu sehr sauberer Luft (AOD 0,05).
  function klarheit(hoch, mittel, tief, aod) {
    const fS = 1 - 0.6 * (hoch || 0) / 100;
    const fD = Math.min(1, Math.exp(-((aod ?? 0.05) - 0.05)));
    const fW = 1 - 0.9 * Math.max(mittel || 0, tief || 0) / 100;
    return { wert: Math.round(100 * fS * fD * fW), schleier: 1 - fS, dunst: 1 - fD, wolken: 1 - fW };
  }

  class HimmelsblickCard extends HTMLElement {
    static getStubConfig() { return { titel: 'Himmel' }; }
    setConfig(c) { this._c = { titel: 'Himmel', ...(c || {}) }; this._sig = null; }
    getCardSize() { return 6; }
    getGridOptions() { return { columns: 12, min_columns: 6, rows: 'auto' }; }

    set hass(h) {
      this._h = h;
      if (!this._e) this._finde();
      const sig = this._e ? Object.values(this._e).map((id) => h.states[id] && h.states[id].last_updated).join('|') + '|' + (this._c.pv ? (h.states[this._c.pv] || {}).state : '') : 'x';
      const jetzt = Date.now();
      if (sig !== this._sig || !this._t || jetzt - this._t > 60000) { this._sig = sig; this._t = jetzt; this._zeichne(); }
    }

    _finde() {
      const reg = (this._h && this._h.entities) || {};
      const e = {};
      for (const x of Object.values(reg)) {
        if (x.platform !== 'himmelsblick' || !x.translation_key) continue;
        if (this._c.geraet && x.device_id !== this._c.geraet) continue;
        if (!e[x.translation_key]) e[x.translation_key] = x.entity_id;
      }
      this._e = Object.keys(e).length ? e : null;
    }

    _v(k) { const id = this._e && this._e[k]; const s = id && this._h.states[id]; const x = s ? parseFloat(s.state) : NaN; return isNaN(x) ? null : x; }
    _n(x, d = 0) { return x === null || x === undefined ? '–' : Number(x).toLocaleString('de-DE', { minimumFractionDigits: d, maximumFractionDigits: d }); }

    _zeichne() {
      if (!this._card) {
        this._card = document.createElement('ha-card');
        this.appendChild(this._card);
      }
      if (!this._e) { this._card.innerHTML = `<div style="padding:16px">Himmelsblick: keine Sensoren gefunden – ist die Integration eingerichtet?</div>`; return; }
      const hoch = this._v('wolken_hoch'), mittel = this._v('wolken_mittel'), tief = this._v('wolken_tief');
      const aod = this._v('aerosol'), staub = this._v('staub'), pm = this._v('feinstaub');
      const ghi = this._v('strahlung'), klar = this._v('klarer_himmel'), sonne = this._v('sonnenhoehe');
      const k = klarheit(hoch, mittel, tief, aod);
      const urs = [['Schleier (hohe Wolken)', k.schleier, '#90caf9'], ['Dunst/Staub', k.dunst, '#ffcc80'], ['Wolken', k.wolken, '#b0bec5']].sort((a, b) => b[1] - a[1]);
      const text = k.wert >= 85 ? 'Klarer Himmel' : k.wert >= 65 ? 'Leicht trüb' : k.wert >= 40 ? (urs[0][0].startsWith('Wolken') ? 'Teils bewölkt' : 'Milchiger Himmel') : 'Bedeckt';
      const farbe = k.wert >= 85 ? '#29b6f6' : k.wert >= 65 ? '#66bb6a' : k.wert >= 40 ? '#ffb74d' : '#90a4ae';
      const tag = klar !== null && klar > 30;
      const sonnenAnteil = tag && ghi !== null ? Math.min(120, Math.round(100 * ghi / klar)) : null;
      // PV-Vergleich (optional): Ist-Leistung gegen grobe Erwartung bei klarem Himmel
      let pvAnteil = null;
      if (this._c.pv && this._c.pv_kwp && tag && klar > 80) {
        const s = this._h.states[this._c.pv]; const pv = s ? parseFloat(s.state) : NaN;
        if (!isNaN(pv)) pvAnteil = Math.min(150, Math.round(100 * pv / (this._c.pv_kwp * klar * 0.8)));
      }
      const ring = (w) => { const r = 54, u = 2 * Math.PI * r; return `<svg viewBox="0 0 140 140" width="132" height="132"><circle cx="70" cy="70" r="${r}" fill="none" stroke="var(--divider-color,#3334)" stroke-width="12"/><circle cx="70" cy="70" r="${r}" fill="none" stroke="${farbe}" stroke-width="12" stroke-linecap="round" stroke-dasharray="${u * w / 100} ${u}" transform="rotate(-90 70 70)"/><text x="70" y="74" text-anchor="middle" font-size="34" font-weight="700" fill="var(--primary-text-color)">${w}</text><text x="70" y="98" text-anchor="middle" font-size="13" fill="var(--secondary-text-color)">von 100</text></svg>`; };
      const balken = (n, w, f, info) => `<div class="z"><span>${n}</span><span class="b"><i style="width:${Math.max(0, Math.min(100, w))}%;background:${f}"></i></span><b>${info}</b></div>`;
      const kamera = this._c.kamera && this._h.states[this._c.kamera] ? `<img class="cam" src="${this._h.states[this._c.kamera].attributes.entity_picture}&t=${Math.floor(Date.now() / 60000)}" alt="Himmel">` : '';

      this._card.innerHTML = `<style>
        .hb{padding:16px;color:var(--primary-text-color)} .kopf{display:flex;justify-content:space-between;align-items:baseline}
        .tt{font-size:20px;font-weight:600} .st{color:var(--secondary-text-color);font-size:13px}
        .oben{display:flex;gap:18px;align-items:center;margin:8px 0}.wert{font-size:22px;font-weight:600;color:${farbe}}
        .z{display:grid;grid-template-columns:150px 1fr 92px;gap:10px;align-items:center;font-size:14px;margin:6px 0}
        .z b{text-align:right;font-variant-numeric:tabular-nums}.b{height:10px;border-radius:5px;background:var(--divider-color,#3334);overflow:hidden}.b i{display:block;height:100%;border-radius:5px}
        .kz{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin-top:10px}
        .kz div{background:var(--secondary-background-color,#0001);border-radius:10px;padding:8px 10px}.kz b{display:block;font-size:18px}.kz span{font-size:12px;color:var(--secondary-text-color)}
        .cam{width:100%;border-radius:12px;margin-top:10px} svg.vl{width:100%;height:auto;margin-top:8px}
        .lg{display:flex;gap:14px;font-size:12px;color:var(--secondary-text-color);flex-wrap:wrap}.lg i{display:inline-block;width:12px;height:10px;border-radius:2px;margin-right:4px}
        @media (max-width:420px){.z{grid-template-columns:110px 1fr 70px}}
      </style>
      <div class="hb">
        <div class="kopf"><span class="tt">${this._c.titel}</span><span class="st">Himmelsklarheit</span></div>
        <div class="oben">${ring(k.wert)}<div><div class="wert">${text}</div>
          <div class="st">${tag ? `Sonne kommt an: <b>${this._n(sonnenAnteil)} %</b> der Strahlung bei klarem Himmel${pvAnteil !== null ? `<br>PV liefert ca. <b>${pvAnteil} %</b> des Möglichen` : ''}` : `Sonne unter dem Horizont (${this._n(sonne, 0)}°)`}</div>
          <div class="st" style="margin-top:4px">Hauptursache: ${urs[0][1] < 0.08 ? 'nichts Nennenswertes' : urs[0][0]}</div></div></div>
        ${balken('Schleier (hoch)', hoch, '#90caf9', this._n(hoch) + ' %')}
        ${balken('Mittelhohe Wolken', mittel, '#b0bec5', this._n(mittel) + ' %')}
        ${balken('Tiefe Wolken', tief, '#78909c', this._n(tief) + ' %')}
        ${balken('Dunst (AOD)', aod === null ? 0 : aod / 0.8 * 100, '#ffcc80', this._n(aod, 2))}
        <div class="kz">
          <div><b>${this._n(ghi)} W/m²</b><span>Strahlung jetzt</span></div>
          <div><b>${this._n(klar)} W/m²</b><span>bei klarem Himmel</span></div>
          <div><b>${this._n(staub)} µg/m³</b><span>Saharastaub</span></div>
          <div><b>${this._n(pm, 1)} µg/m³</b><span>Feinstaub PM2,5</span></div>
        </div>
        ${this._verlauf()}
        ${kamera}
      </div>`;
    }

    _verlauf() {
      const id = this._e.verlauf; const s = id && this._h.states[id];
      const st = s && s.attributes.stunden; if (!st || st.length < 2) return '';
      const W = 480, H = 150, L = 30, R = W - 30, T = 10, B = H - 22, n = st.length;
      const X = (i) => L + (i + 0.5) * (R - L) / n, Y = (p) => B - p / 100 * (B - T);
      const maxS = Math.max(200, ...st.map((x) => Math.max(x.klar || 0, x.ghi || 0)));
      const YS = (w) => B - w / maxS * (B - T);
      const bw = (R - L) / n * 0.7, jetzt = new Date().getHours();
      let g = '';
      for (const p of [0, 50, 100]) g += `<line x1="${L}" x2="${R}" y1="${Y(p)}" y2="${Y(p)}" stroke="var(--divider-color,#3334)"/><text x="${L - 4}" y="${Y(p) + 4}" font-size="10" text-anchor="end" fill="var(--secondary-text-color)">${p}</text>`;
      st.forEach((x, i) => { g += `<rect x="${X(i) - bw / 2}" y="${Y(x.hoch || 0)}" width="${bw}" height="${B - Y(x.hoch || 0)}" fill="#90caf9" opacity=".45"/>`; if (x.t % 3 === 0) g += `<text x="${X(i)}" y="${H - 6}" font-size="10" text-anchor="middle" fill="var(--secondary-text-color)">${String(x.t).padStart(2, '0')}</text>`; });
      const pfad = (f) => st.map((x, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)},${f(x).toFixed(1)}`).join(' ');
      g += `<path d="${pfad((x) => YS(x.klar || 0))}" fill="none" stroke="#ffd54f" stroke-width="1.5" stroke-dasharray="4 3"/>`;
      g += `<path d="${pfad((x) => YS(x.ghi || 0))} L${X(n - 1)},${B} L${X(0)},${B} Z" fill="#ffb30033"/>`;
      g += `<path d="${pfad((x) => Y(klarheit(x.hoch, x.mittel, x.tief, x.aod).wert))}" fill="none" stroke="#29b6f6" stroke-width="2.5"/>`;
      const ji = st.findIndex((x) => x.t === jetzt);
      if (ji >= 0) g += `<line x1="${X(ji)}" x2="${X(ji)}" y1="${T}" y2="${B}" stroke="var(--primary-text-color)" stroke-dasharray="3 3" opacity=".5"/>`;
      return `<svg class="vl" viewBox="0 0 ${W} ${H}">${g}</svg>
        <div class="lg"><span><i style="background:#29b6f6"></i>Klarheit</span><span><i style="background:#90caf9;opacity:.6"></i>Schleier (hohe Wolken)</span><span><i style="background:#ffb30066"></i>Strahlung</span><span><i style="border-top:2px dashed #ffd54f;height:0"></i>klarer Himmel</span></div>`;
    }
  }

  customElements.define('himmelsblick-card', HimmelsblickCard);
  window.customCards = window.customCards || [];
  window.customCards.push({ type: 'himmelsblick-card', name: 'Himmelsblick', description: 'Himmelsklarheit: Schleier, Dunst, Wolken und Sonnenstrahlung', preview: true });
  console.info(`%c HIMMELSBLICK %c ${VERSION} `, 'background:#29b6f6;color:#000', 'background:#333;color:#fff');
})();
