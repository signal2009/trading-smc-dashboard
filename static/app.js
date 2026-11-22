/* ── TAB SWITCHING ── */
function switchTab(tab, el){
    document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));
    document.getElementById('tab-'+tab).classList.add('active');
    el.classList.add('active');
}

/* ── TAB 1: MARKET ANALYSIS ── */
let maData=null;
async function azM(s, el){
    const panel=document.getElementById('tab-market');
    panel.querySelectorAll('.ib').forEach(b=>b.classList.remove('active'));
    if(el) el.classList.add('active');
    document.getElementById('mp-market').innerHTML=`<div class="loading"><div class="spinner"></div><p style="color:#8b949e">Analyzing 6 months...</p></div>`;
    try{
        const r=await fetch('/api/market/'+s);const d=await r.json();
        if(d.success){maData=d.analysis;renderMarket(d.analysis)}
        else{document.getElementById('mp-market').innerHTML=`<div class="err">${d.message}</div>`}
    }catch(e){document.getElementById('mp-market').innerHTML=`<div class="err">${e.message}</div>`}
}
function renderMarket(a){
    const sc=a.signals.primary_signal.toLowerCase().replace(' ','-');
    const vr=a.volume_ratio||1;const vc=vr>1.5?'positive':vr<0.5?'negative':'neutral';
    let h=`<div class="ma-header"><div><h2 style="color:#f0f6fc">${a.symbol}</h2><div class="ma-price">$${a.current_price}</div>
        <div style="margin-top:8px"><span class="${a.change_24h>0?'positive':'negative'}">24h: ${a.change_24h>0?'+':''}${a.change_24h}%</span>
        <span style="margin-left:16px" class="${a.change_7d>0?'positive':'negative'}">7d: ${a.change_7d>0?'+':''}${a.change_7d}%</span>
        <span style="margin-left:16px" class="${a.change_30d>0?'positive':'negative'}">30d: ${a.change_30d>0?'+':''}${a.change_30d}%</span></div>
        </div><div><div class="sig-badge sig-${sc}">${a.signals.primary_signal}</div>
        <div style="text-align:center;margin-top:6px;color:#8b949e;font-size:12px">Strength: ${a.signals.strength}/10</div></div></div>
        <div class="ind-grid">
        <div class="ind-card"><div class="ind-label">Trend</div><div class="ind-val ${a.trend==='Bullish'?'positive':a.trend==='Bearish'?'negative':'neutral'}">${a.trend}</div></div>
        <div class="ind-card"><div class="ind-label">RSI (14)</div><div class="ind-val ${a.rsi<30?'positive':a.rsi>70?'negative':'neutral'}">${a.rsi}</div></div>
        <div class="ind-card"><div class="ind-label">MACD</div><div class="ind-val ${a.macd>a.macd_signal?'positive':'negative'}">${a.macd>a.macd_signal?'Bullish':'Bearish'}</div></div>
        <div class="ind-card"><div class="ind-label">Stoch %K</div><div class="ind-val ${a.stochastic.k<20?'positive':a.stochastic.k>80?'negative':'neutral'}">${a.stochastic.k}</div></div>
        <div class="ind-card"><div class="ind-label">Volume</div><div class="ind-val ${vc}">${vr}x</div></div>
        <div class="ind-card"><div class="ind-label">Volatility</div><div class="ind-val">${a.volatility}%</div></div>
        <div class="ind-card"><div class="ind-label">ATR</div><div class="ind-val">${a.atr}</div></div>
        <div class="ind-card"><div class="ind-label">Vol Trend</div><div class="ind-val ${a.volume_trend==='Increasing'?'positive':'negative'}">${a.volume_trend}</div></div>
        </div>`;
    h+=`<div class="lv-section"><h3>Support & Resistance</h3><h4 style="margin-top:8px">Support</h4><div class="lv-list">
        ${a.support_levels.map(l=>`<div class="lv-item lv-sup">$${l.toFixed(5)}</div>`).join('')}</div>
        <h4 style="margin-top:12px">Resistance</h4><div class="lv-list">
        ${a.resistance_levels.map(l=>`<div class="lv-item lv-res">$${l.toFixed(5)}</div>`).join('')}</div></div>`;
    if(a.patterns.length>0){
        h+=`<div class="lv-section"><h3>Chart Patterns</h3>${a.patterns.map(p=>`<div class="pat-card">
            <strong>${p.name}</strong> (${p.type}, ${p.direction}, ${p.confidence}%)<br>
            Entry: ${p.entry_condition} | Stop: ${p.stop_loss}<br>TP1: ${p.take_profit_1} | TP2: ${p.take_profit_2}</div>`).join('')}</div>`;
    }
    h+=`<div class="lv-section"><h3>EMAs</h3><div class="ind-grid">
        <div class="ind-card"><div class="ind-label">EMA 20</div><div class="ind-val">$${a.ema_20}</div></div>
        <div class="ind-card"><div class="ind-label">EMA 50</div><div class="ind-val">$${a.ema_50}</div></div>
        ${a.ema_200?`<div class="ind-card"><div class="ind-label">EMA 200</div><div class="ind-val">$${a.ema_200}</div></div>`:''}</div></div>`;
    if(a.signals.stop_loss){
        h+=`<div class="lv-section"><h3>Signals</h3><ul style="margin:8px 0;padding-left:20px;font-size:13px">
            ${a.signals.entry_points.map(e=>`<li>${e}</li>`).join('')}</ul>
            <p style="margin-top:8px"><strong>SL:</strong> $${a.signals.stop_loss}</p>
            <div class="lv-list">${(a.signals.take_profit||[]).map((t,i)=>`<div class="lv-item">TP${i+1}: $${t}</div>`).join('')}</div></div>`;
    }
    h+=`<div class="lv-section"><button class="btn btn-b" onclick="genPromptM()">Generate Strategy Prompt</button><div id="mpout"></div></div>`;
    document.getElementById('mp-market').innerHTML=h;
}
function genPromptM(){
    if(!maData)return;const a=maData;
    let p=`${a.symbol} @ $${a.current_price}\nTrend: ${a.trend} | RSI: ${a.rsi} | MACD: ${a.macd>a.macd_signal?'Bull':'Bear'}\n`;
    p+=`Signal: ${a.signals.primary_signal} (${a.signals.strength}/10)\nVolume: ${a.volume_ratio}x\n`;
    p+=`Support: ${a.support_levels.map(x=>'$'+x).join(', ')}\nResistance: ${a.resistance_levels.map(x=>'$'+x).join(', ')}\n`;
    if(a.signals.stop_loss)p+=`SL: $${a.signals.stop_loss} | TP: ${a.signals.take_profit.map(x=>'$'+x).join(', ')}\n`;
    document.getElementById('mpout').innerHTML=`<div class="pbox">${p}</div><button class="btn btn-g" onclick="navigator.clipboard.writeText(document.querySelector('#mpout .pbox').textContent).then(()=>alert('Copied!'))" style="margin-top:6px">Copy</button>`;
}

/* ── TAB 2: SMC HP ── */
let smcData=null;
async function azS(s, el){
    const panel=document.getElementById('tab-smc');
    panel.querySelectorAll('.ib').forEach(b=>b.classList.remove('active'));
    if(el) el.classList.add('active');
    document.getElementById('mp-smc').innerHTML=`<div class="loading"><div class="spinner"></div><p style="color:#8b949e">Scanning structure...</p></div>`;
    try{
        const r=await fetch('/api/smc/'+s);const d=await r.json();
        if(d.success){smcData=d.analysis;renderSMC(d.analysis)}
        else{document.getElementById('mp-smc').innerHTML=`<div class="err">${d.message}</div>`}
    }catch(e){document.getElementById('mp-smc').innerHTML=`<div class="err">${e.message}</div>`}
}
function renderSMC(a){
    const tc=a.trend==='bullish'?'t-bull':a.trend==='bearish'?'t-bear':'t-neut';
    const pz=a.pd_zone;
    const pzc=pz?(pz.zone==='discount'?'grn':'red'):'ylw';
    let h=`<div class="ph"><div><h2 style="color:#f0f6fc">${a.symbol}</h2><div class="pb">$${a.current_price}</div></div>
        <div style="text-align:right"><div class="tb ${tc}">BOS: ${a.trend.toUpperCase()}</div>
        ${pz?`<div style="margin-top:4px"><span class="tb" style="font-size:10px;padding:3px 8px;background:${pz.zone==='discount'?'#0d2818':'#3d0d0d'};color:${pz.zone==='discount'?'#3fb950':'#f85149'};border:1px solid ${pz.zone==='discount'?'#238636':'#da3633'}">${pz.zone.toUpperCase()} ${pz.position_pct}%${pz.in_ote?' • OTE':''}</span></div>`:''}
        <div style="margin-top:4px;color:#8b949e;font-size:11px">${a.data_points} bars | ATR: ${a.atr}</div></div></div>
        <div class="sg">
        <div class="sc"><div class="sl">Bull BOS</div><div class="sv grn">${a.bos_bullish}</div></div>
        <div class="sc"><div class="sl">Bear BOS</div><div class="sv red">${a.bos_bearish}</div></div>
        <div class="sc"><div class="sl">Major</div><div class="sv ylw">${a.major_bos}</div></div>
        <div class="sc"><div class="sl">Sweeps</div><div class="sv pur">${a.total_sweeps}</div></div>
        <div class="sc"><div class="sl">HP OBs</div><div class="sv org">${a.hp_order_blocks}</div></div>
        <div class="sc"><div class="sl">FVGs</div><div class="sv blu">${a.fvg_count||0}</div></div>
        <div class="sc"><div class="sl">CHoCH</div><div class="sv" style="color:#e87d7d">${a.choch_count||0}</div></div>
        <div class="sc"><div class="sl">EQH/EQL</div><div class="sv" style="color:#c9a0dc">${(a.eq_high_count||0)+(a.eq_low_count||0)}</div></div></div>
        <div class="cnt-badges"><span class="cnt-b b1">S1: ${a.s1_count}</span><span class="cnt-b b2">S2: ${a.s2_count}</span><span class="cnt-b b3">S3: ${a.s3_count}</span></div>`;
    // ═══ DIRECTION CONFIRMATION — THE MAIN EVENT ═══
    if(a.direction){
        const dir=a.direction;
        const isBull=dir.verdict.includes('BULL');
        const isBear=dir.verdict.includes('BEAR');
        const isStrong=dir.verdict.includes('STRONG');
        const bgc=isBull?'#0a1f0a':isBear?'#1f0a0a':'#1a1a0a';
        const brc=isBull?'#238636':isBear?'#da3633':'#9e6a03';
        const txc=isBull?'#3fb950':isBear?'#f85149':'#d29922';
        const barW=Math.min(Math.abs(dir.direction_score),100);
        const barDir=dir.direction_score>=0?'right':'left';
        h+=`<div class="section" style="background:${bgc};border:2px solid ${brc};padding:20px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                <h3 style="color:${txc};font-size:1.1rem;margin:0">DIRECTION CONFIRMATION</h3>
                <div style="display:flex;align-items:center;gap:10px">
                    <span style="font-size:2rem;font-weight:900;color:${txc}">${dir.verdict}</span>
                    <span style="font-size:1.5rem;font-weight:900;color:${txc};background:${bgc};border:2px solid ${brc};padding:4px 14px;border-radius:8px">${dir.direction_score>0?'+':''}${dir.direction_score}</span>
                </div>
            </div>
            <div style="background:#0d1117;border-radius:6px;height:28px;position:relative;overflow:hidden;margin-bottom:14px">
                <div style="position:absolute;left:50%;top:0;bottom:0;width:2px;background:#484f58;z-index:2"></div>
                <div style="position:absolute;${dir.direction_score>=0?'left:50%':'right:50%'};top:2px;bottom:2px;width:${barW/2}%;background:${txc};border-radius:3px;transition:width 0.5s"></div>
                <div style="position:absolute;left:8px;top:4px;font-size:10px;color:#f85149;font-weight:700">BEAR</div>
                <div style="position:absolute;right:8px;top:4px;font-size:10px;color:#3fb950;font-weight:700">BULL</div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
                <div>
                    <div style="font-size:10px;color:#3fb950;font-weight:700;margin-bottom:6px">BULLISH (${dir.bull_count})</div>
                    ${dir.bull_factors.map(f=>'<div style="padding:3px 8px;background:#0d2818;border-radius:3px;font-size:10px;margin-bottom:3px;border-left:2px solid #238636;color:#3fb950">'+f+'</div>').join('')}
                </div>
                <div>
                    <div style="font-size:10px;color:#f85149;font-weight:700;margin-bottom:6px">BEARISH (${dir.bear_count})</div>
                    ${dir.bear_factors.map(f=>'<div style="padding:3px 8px;background:#3d0d0d;border-radius:3px;font-size:10px;margin-bottom:3px;border-left:2px solid #da3633;color:#f85149">'+f+'</div>').join('')}
                </div>
            </div>
            ${dir.neutral_factors.length>0?`<div style="margin-top:8px"><div style="font-size:10px;color:#d29922;font-weight:700;margin-bottom:4px">NEUTRAL (${dir.neutral_count})</div>${dir.neutral_factors.map(f=>'<span style="padding:2px 6px;background:#2d1f00;border-radius:3px;font-size:9px;margin-right:4px;color:#d29922">'+f+'</span>').join('')}</div>`:''}
        </div>`;
    }
    if(a.all_signals&&a.all_signals.length>0){
        h+=`<div class="section"><h3>Signals (${a.signal_count})</h3>`;
        for(const s of a.all_signals){
            const dc=s.direction==='BUY'?'buy':'sell';const dcol=s.direction==='BUY'?'grn':'red';
            const cc=s.confidence>=75?'ch':s.confidence>=60?'cm':'cl';
            const stc=s.strategy==='Strategy 1'?'st1':s.strategy==='Strategy 2'?'st2':'st3';
            const cg=s.confluence_grade||'?';const cs=s.confluence_score||0;
            const gc=cg==='A+'?'#ffd700':cg==='A'?'#3fb950':cg==='B+'?'#58a6ff':cg==='B'?'#8b949e':'#484f58';
            h+=`<div class="sigcard ${dc}"><div class="sh-h"><div><span class="stag ${stc}">${s.strategy}</span><span class="sd ${dcol}">${s.direction}</span>
                <span style="color:#8b949e;font-size:11px;margin-left:5px">${s.signal_type}</span></div>
                <div style="display:flex;gap:6px;align-items:center">
                <span style="background:#0d1117;border:2px solid ${gc};color:${gc};padding:3px 10px;border-radius:6px;font-weight:800;font-size:14px">${cg}</span>
                <span style="font-size:10px;color:${gc}">${cs} conf</span>
                <div class="sconf ${cc}">${s.confidence}%</div></div></div>
                <div class="sgrid"><div class="si"><div class="sil">Entry</div><div class="siv">$${s.entry_price}</div></div>
                <div class="si"><div class="sil">Zone</div><div class="siv" style="font-size:10px">${s.entry_zone}</div></div>
                <div class="si"><div class="sil">SL</div><div class="siv red">$${s.stop_loss}</div></div>
                <div class="si"><div class="sil">TP1</div><div class="siv grn">$${s.take_profit_1}</div></div>
                <div class="si"><div class="sil">TP2</div><div class="siv grn">$${s.take_profit_2}</div></div>
                <div class="si"><div class="sil">TP3</div><div class="siv grn">$${s.take_profit_3}</div></div>
                <div class="si"><div class="sil">Risk</div><div class="siv">${s.risk_pct}%</div></div>
                <div class="si"><div class="sil">BOS</div><div class="siv">${s.ob_atr_ratio}x ATR</div></div></div>
                <div class="fl">${(s.factors||[]).map(f=>'<div class="fi">'+f+'</div>').join('')}</div></div>`;
        }h+=`</div>`;
    }else{h+=`<div class="section"><div class="ns"><h3>No HP Signals</h3><p style="font-size:12px">Price not in validated OB zone or conditions not met</p></div></div>`}
    if(a.recent_bos&&a.recent_bos.length>0){
        h+=`<div class="section"><h3>Recent BOS</h3><div style="display:flex;flex-wrap:wrap;gap:3px">`;
        for(const b of a.recent_bos){h+=`<span class="bi ${b.direction==='bullish'?'bb':'bs'} ${b.major?'bm':''}">${b.direction.toUpperCase()} $${b.level} ${b.major?'★ ':''}${b.atr_ratio}x</span>`}
        h+=`</div></div>`}
    if(a.active_obs&&a.active_obs.length>0){
        h+=`<div class="section"><h3>Active OBs (HP)</h3>`;
        for(const o of a.active_obs){h+=`<div class="obi ${o.direction==='bullish'?'ob-b':'ob-s'}"><span>${o.direction.toUpperCase()}</span><span>${o.zone}</span><span class="ylw">${o.atr_ratio}x</span><span style="color:#484f58">${o.tested?'Tested '+o.test_count+'x':'Fresh'}</span></div>`}
        h+=`</div>`}
    if(a.liquidity_zones&&a.liquidity_zones.length>0){
        h+=`<div class="section"><h3>Liquidity Zones</h3>`;
        for(const z of a.liquidity_zones){h+=`<div class="lz ${z.type==='support'?'lz-sup':'lz-res'}"><span>${z.type.toUpperCase()}</span><span>${z.zone}</span><span>${z.touches} touches</span></div>`}
        h+=`</div>`}
    h+=`<div class="section"><h3>Protected Levels</h3><div class="sg">`;
    (a.protected_lows||[]).forEach(p=>{h+=`<div class="sc"><div class="sl">Low (${p.touches}t)</div><div class="sv grn">$${p.price}</div></div>`});
    (a.protected_highs||[]).forEach(p=>{h+=`<div class="sc"><div class="sl">High (${p.touches}t)</div><div class="sv red">$${p.price}</div></div>`});
    h+=`</div></div>`;
    if(a.recent_sweeps&&a.recent_sweeps.length>0){
        h+=`<div class="section"><h3>Sweeps</h3>`;
        for(const s of a.recent_sweeps){h+=`<div class="obi"><span class="${s.type.includes('bullish')?'grn':'red'}">${s.type.replace('_',' ').toUpperCase()}</span><span>$${s.level}</span><span>${s.deep?'<span class="ylw">DEEP</span>':''} ${s.caused_bos?'<span class="org">+BOS</span>':''}</span></div>`}
        h+=`</div>`}
    // NEW: Premium/Discount Zone
    if(a.pd_zone){
        const pz=a.pd_zone;const zc=pz.zone==='discount'?'grn':'red';
        h+=`<div class="section"><h3>Premium / Discount Zone</h3>
        <div class="sg">
            <div class="sc"><div class="sl">Swing High</div><div class="sv red">$${pz.swing_high}</div></div>
            <div class="sc"><div class="sl">78.6% Fib</div><div class="sv" style="color:#c9a0dc">$${pz.fib_786}</div></div>
            <div class="sc"><div class="sl">61.8% Fib</div><div class="sv" style="color:#c9a0dc">$${pz.fib_618}</div></div>
            <div class="sc"><div class="sl">Equilibrium</div><div class="sv ylw">$${pz.equilibrium}</div></div>
            <div class="sc"><div class="sl">38.2% Fib</div><div class="sv" style="color:#7da8e8">$${pz.fib_382}</div></div>
            <div class="sc"><div class="sl">Swing Low</div><div class="sv grn">$${pz.swing_low}</div></div>
        </div>
        <div style="display:flex;gap:8px;margin-top:6px;align-items:center">
            <span style="font-size:12px;font-weight:700" class="${zc}">Price in ${pz.zone.toUpperCase()} (${pz.position_pct}%)</span>
            ${pz.in_ote?'<span style="background:#1c0d35;color:#bc8cff;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700">INSIDE OTE (61.8-78.6%)</span>':''}
            <span style="font-size:10px;color:#484f58">${pz.zone==='discount'?'BUY bias — below equilibrium':'SELL bias — above equilibrium'}</span>
        </div></div>`;
    }
    // NEW: Weighted Volume POC
    if(a.poc){
        const poc=a.poc;
        const pc=poc.above_poc?'grn':'red';
        h+=`<div class="section"><h3>Weighted Volume POC (Point of Control)</h3>
        <div class="sg">
            <div class="sc"><div class="sl">POC Price</div><div class="sv ylw">$${poc.poc_price}</div></div>
            <div class="sc"><div class="sl">Value Area H</div><div class="sv red">$${poc.vah}</div></div>
            <div class="sc"><div class="sl">Value Area L</div><div class="sv grn">$${poc.val}</div></div>
            <div class="sc"><div class="sl">Buyers</div><div class="sv grn">${poc.poc_bull_pct}%</div></div>
            <div class="sc"><div class="sl">Sellers</div><div class="sv red">${poc.poc_bear_pct}%</div></div>
            <div class="sc"><div class="sl">Dist to POC</div><div class="sv ${pc}">${poc.poc_atr_dist}x ATR</div></div>
        </div>
        <div style="display:flex;gap:8px;margin-top:6px;align-items:center;font-size:11px">
            <span class="${pc}" style="font-weight:700">${poc.above_poc?'ABOVE':'BELOW'} POC</span>
            <span style="color:#484f58">${poc.price_in_value_area?'Inside value area — range-bound':'Outside value area — trending'}</span>
        </div></div>`;
    }
    // NEW: Fair Value Gaps
    if(a.fvgs&&a.fvgs.length>0){
        h+=`<div class="section"><h3>Fair Value Gaps (Unmitigated)</h3>`;
        for(const f of a.fvgs){h+=`<div class="obi ${f.direction==='bullish'?'ob-b':'ob-s'}"><span>${f.direction.toUpperCase()} FVG</span><span>${f.zone}</span><span class="ylw">${f.atr_ratio}x ATR</span></div>`}
        h+=`</div>`}
    // NEW: CHoCH
    if(a.choch&&a.choch.length>0){
        h+=`<div class="section"><h3>Change of Character (CHoCH)</h3><div style="display:flex;flex-wrap:wrap;gap:3px">`;
        for(const c of a.choch){h+=`<span class="bi ${c.direction==='bullish'?'bb':'bs'} ${c.major?'bm':''}">${c.from}→${c.direction.toUpperCase()} $${c.level} ${c.major?'★':''}</span>`}
        h+=`</div></div>`}
    // NEW: Equal Highs / Equal Lows
    if((a.equal_highs&&a.equal_highs.length>0)||(a.equal_lows&&a.equal_lows.length>0)){
        h+=`<div class="section"><h3>Equal Highs / Equal Lows (Liquidity Clusters)</h3>`;
        if(a.equal_highs){for(const e of a.equal_highs){h+=`<div class="obi ob-s"><span>EQH ×${e.count}</span><span>$${e.level}</span><span>${e.swept?'<span class="org">SWEPT</span>':'<span class="red">TARGET</span>'}</span></div>`}}
        if(a.equal_lows){for(const e of a.equal_lows){h+=`<div class="obi ob-b"><span>EQL ×${e.count}</span><span>$${e.level}</span><span>${e.swept?'<span class="org">SWEPT</span>':'<span class="grn">TARGET</span>'}</span></div>`}}
        h+=`</div>`}
    // Trendlines
    if(a.trendlines&&a.trendlines.length>0){
        h+=`<div class="section"><h3>Trendlines</h3>`;
        for(const t of a.trendlines){
            const tc2=t.type==='ascending'?'grn':'red';
            const near=t.near_trendline;
            h+=`<div class="obi" style="border-left:3px solid ${t.type==='ascending'?'#3fb950':'#f85149'}">
                <span class="${tc2}" style="font-weight:700">${t.type.toUpperCase()}</span>
                <span>${t.touches} touches</span>
                <span>Projected: $${t.projected_price}</span>
                <span>${t.distance_atr}x ATR away</span>
                ${near?'<span style="background:#1c0d35;color:#bc8cff;padding:2px 6px;border-radius:3px;font-size:10px;font-weight:700">PRICE AT LINE</span>':''}
            </div>`;
        }
        h+=`</div>`}
    // Confluence grading legend
    h+=`<div class="section" style="background:#010409;border:1px solid #21262d">
        <h3 style="margin-bottom:8px">Confluence Grade Key</h3>
        <div style="display:flex;flex-wrap:wrap;gap:8px;font-size:11px">
            <span style="border:2px solid #ffd700;color:#ffd700;padding:3px 10px;border-radius:6px;font-weight:800">A+ (7+)</span>
            <span style="border:2px solid #3fb950;color:#3fb950;padding:3px 10px;border-radius:6px;font-weight:800">A (5-6)</span>
            <span style="border:2px solid #58a6ff;color:#58a6ff;padding:3px 10px;border-radius:6px;font-weight:800">B+ (4)</span>
            <span style="border:2px solid #8b949e;color:#8b949e;padding:3px 10px;border-radius:6px;font-weight:800">B (3)</span>
            <span style="border:2px solid #484f58;color:#484f58;padding:3px 10px;border-radius:6px;font-weight:800">C (2)</span>
        </div>
        <div style="margin-top:8px;color:#484f58;font-size:10px">
            Factors: OB zone • FVG • Premium/Discount • OTE • Liq Sweep • Deep Sweep • CHoCH • Trendline • EQH/EQL • Impulsive BOS
        </div>
    </div>`;
    h+=`<div class="section"><button class="btn btn-b" onclick="genPromptS()">Generate Prompt</button><div id="spout"></div></div>`;
    document.getElementById('mp-smc').innerHTML=h;
}
function genPromptS(){
    if(!smcData)return;const a=smcData,b=a.best_signal;
    let p=`SMC — ${a.symbol} @ $${a.current_price}\nATR: ${a.atr} | Trend: ${a.trend.toUpperCase()}\n`;
    if(a.direction){p+=`⚡ DIRECTION: ${a.direction.verdict} (${a.direction.direction_score>0?'+':''}${a.direction.direction_score})\n  Bull factors: ${a.direction.bull_count} | Bear factors: ${a.direction.bear_count}\n`}
    p+=`BOS: Bull=${a.bos_bullish} Bear=${a.bos_bearish} Major=${a.major_bos}\nHP OBs: ${a.hp_order_blocks} | Sweeps: ${a.total_sweeps} | FVGs: ${a.fvg_count||0} | CHoCH: ${a.choch_count||0}\n`;
    if(a.poc){p+=`POC: $${a.poc.poc_price} (${a.poc.above_poc?'above':'below'}) | VAH: $${a.poc.vah} | VAL: $${a.poc.val}\n`}
    if(a.pd_zone){p+=`Zone: ${a.pd_zone.zone.toUpperCase()} (${a.pd_zone.position_pct}%) | EQ: $${a.pd_zone.equilibrium}${a.pd_zone.in_ote?' | IN OTE':''}\n`}
    p+=`EQH: ${a.eq_high_count||0} | EQL: ${a.eq_low_count||0}\n\n`;
    if(b){p+=`SIGNAL: ${b.direction} (${b.strategy})\nConf: ${b.confidence}% | Entry: $${b.entry_price}\nZone: ${b.entry_zone}\nSL: $${b.stop_loss} | TP1: $${b.take_profit_1} | TP2: $${b.take_profit_2}\n`;(b.factors||[]).forEach(f=>{p+=`• ${f}\n`})}
    else{p+=`NO HP SIGNALS\n`}
    document.getElementById('spout').innerHTML=`<div class="pbox">${p}</div><button class="btn btn-g" onclick="navigator.clipboard.writeText(document.querySelector('#spout .pbox').textContent).then(()=>alert('Copied!'))" style="margin-top:6px">Copy</button>`;
}
