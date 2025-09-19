// —— DOM & utils —— //
const $ = (s)=>document.querySelector(s);
function range(a,b){const r=[];for(let x=a;x<=b;x++)r.push(x);return r;}
function isLeap(y){return (y%4===0&&y%100!==0)||(y%400===0);}
function daysInMonth(y,m){return [31,(isLeap(y)?29:28),31,30,31,30,31,31,30,31,30,31][m-1];}
function fillOptions(sel, arr, defVal){sel.innerHTML="";arr.forEach(v=>{const o=document.createElement("option");o.value=String(v);o.textContent=String(v);if(v===defVal)o.selected=true;sel.appendChild(o);});}
function updateDayOptions(){const y=+$("#year").value,m=+$("#month").value,dm=daysInMonth(y,m),cur=+($("#day").value||1);fillOptions($("#day"),range(1,dm),Math.min(cur,dm));}
function q(v){return encodeURIComponent(v);}

// —— 初始化下拉 —— //
function initSelects(){
  const now=new Date();
  fillOptions($("#year"), range(1900, now.getFullYear()), now.getFullYear());
  fillOptions($("#month"), range(1,12), now.getMonth()+1);
  updateDayOptions();
  fillOptions($("#hour"), range(0,23), 12);
  fillOptions($("#minute"), range(0,59), 0);
}
$("#year").addEventListener("change", updateDayOptions);
$("#month").addEventListener("change", updateDayOptions);

// —— API —— //
async function fetchChart(){
  const y=$("#year").value,m=$("#month").value,d=$("#day").value,h=$("#hour").value,mi=$("#minute").value;
  const loc=$("#location").value, hsys=$("#house_system").value;
  $("#status").textContent="計算中…";
  const url=`/api/chart?year=${y}&month=${m}&day=${d}&hour=${h}&minute=${mi}&location=${q(loc)}&house_system=${q(hsys)}`;
  const r=await fetch(url);
  if(!r.ok){$("#status").textContent=`錯誤 ${r.status}`;return;}
  const data=await r.json();
  $("#status").textContent="完成";
  renderAll(data);
}

// —— AstroChart 資料整形 —— //
function toAstroChartData(api){
  const map = {
    "太陽":"Sun","月亮":"Moon","水星":"Mercury","金星":"Venus","火星":"Mars",
    "木星":"Jupiter","土星":"Saturn","天王星":"Uranus","海王星":"Neptune","冥王星":"Pluto"
  };
  const planets = {};
  // 行星
  for (const k in api.planet_lons) {
    const en = map[k];
    if (en) planets[en] = [ Number(api.planet_lons[k]) ];
  }
  // 角度點也納入相位
  planets["Ascendant"] = [ Number(api.asc) ];

  const cusps = (api.cusps || []).slice(0,12).map(Number);
  return { planets, cusps };
}


// —— AstroChart 繪圖（含相位） —— //
function drawAstroChart(api){
  const paper = document.getElementById("paper");
  paper.innerHTML = "";

  const ChartCtor = window.Chart
    || (window.astrochart && window.astrochart.Chart)
    || (window.AstroChart && window.AstroChart.Chart);
  if (!ChartCtor) return;

  const size = paper.clientWidth || 800;
  const chart = new ChartCtor("paper", size, size, {
    show_planet_degrees: true,
    show_cusp_degrees: true
  });

  const data = toAstroChartData(api);
  const radix = chart.radix(data);

  // 先畫盤
  if (typeof radix.draw === "function") radix.draw();

  // 再畫相位（先嘗試內建，再退回自訂）
  if (typeof radix.aspects === "function") {
    let asp = null;
    try { asp = radix.aspects(); } catch(e){}
    if (!asp) {
      try {
        asp = radix.aspects([
          { angle: 0,   orb: 8 },
          { angle: 60,  orb: 4 },
          { angle: 90,  orb: 6 },
          { angle: 120, orb: 7 },
          { angle: 180, orb: 8 }
        ]);
      } catch(e){}
    }
    if (asp && typeof asp.draw === "function") asp.draw();
  }
}

// —— 表格公用 —— //
function fillTable(sel, headers, rows){
  const tbl=document.querySelector(sel); tbl.innerHTML="";
  const thead=document.createElement("thead"); const trh=document.createElement("tr");
  headers.forEach(h=>{const th=document.createElement("th"); th.textContent=h; trh.appendChild(th);});
  thead.appendChild(trh); tbl.appendChild(thead);
  const tbody=document.createElement("tbody");
  rows.forEach(r=>{
    const tr=document.createElement("tr");
    headers.forEach(h=>{
      const td=document.createElement("td");
      const v = r[h] ?? r[h.toLowerCase()] ?? "";
      td.textContent = v;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  tbl.appendChild(tbody);
}

// —— 位置格式化（含秒）與星座 emoji —— //
const SIGN_EMOJI = {
  "牡羊":"♈","金牛":"♉","雙子":"♊","巨蟹":"♋","獅子":"♌","處女":"♍",
  "天秤":"♎","天蠍":"♏","射手":"♐","魔羯":"♑","水瓶":"♒","雙魚":"♓"
};
function norm360(x){x%=360;return x<0?x+360:x;}
function dmsInSign(totalDeg){
  const within = norm360(totalDeg)%30;
  let d = Math.floor(within);
  let mFloat = (within - d)*60;
  let m = Math.floor(mFloat);
  let s = Math.round((mFloat - m)*60);
  if (s===60){s=0;m+=1;}
  if (m===60){m=0;d+=1;}
  if (d===30){d=0;}
  return {d, m, s};
}
function pad2(n){return String(n).padStart(2,"0");}

// —— positions_rows 視圖調整 —— //
function buildPositionsView(api){
  const rows = (api.positions_rows||[]);
  const out = [];
  for (const r of rows){
    const name = r["行星"];
    const sym  = (api.symbols && api.symbols[name]) || "";

    let lonDeg, sign;
    if (name === "上升"){ lonDeg = api.asc; sign = api.asc_sign; }
    else if (name === "天頂"){ lonDeg = api.mc; sign = api.mc_sign; }
    else { lonDeg = api.planet_lons[name]; sign = api.planet_signs[name]; }

    const {d,m,s} = dmsInSign(lonDeg);
    const emoji = SIGN_EMOJI[sign] || "";
    const posStr = `${emoji} ${pad2(d)}°${pad2(m)}′${pad2(s)}″ ${sign}座`;

    const status = (!r["黃道狀態"] || String(r["黃道狀態"]).includes("無傳統")) ? "-" : r["黃道狀態"];

    out.push({
      "Symbol": sym,
      "行星": name,
      "位置": posStr,
      "落宮": r["落宮"],
      "守護宮": r["守護宮"] || "-",
      "黃道狀態": status
    });
  }
  return out;
}

// —— 渲染 —— //
function renderAll(data){
  $("#geo").textContent=`lat=${data.geo.lat.toFixed(5)}, lon=${data.geo.lon.toFixed(5)}, tz=${data.geo.tz}`;
  $("#hsys").textContent=data.house_system_cn || "";

  fillTable("#four_kings", ["項目","宮位","屬性","說明"], data.four_kings);
  fillTable("#summary_rows", ["元素","簡介","總分"], data.summary_rows);
  fillTable("#detail_rows", ["Item","Symbol","Constellation","Element","Score"], data.detail_rows);
  fillTable("#aspects_rows", ["組合","類型","偏離角度"], data.aspects_rows || []);

  // 宮位狀態：[宮位, 宮名, 宮位意涵, 宮位星座, 宮中行星]
  const houses = (data.houses_rows||[]).map(r=>{
    const planets = r["宮中行星"];
    return {
      "宮位": r["宮位"],
      "宮名": r["宮名"],
      "宮位意涵": r["宮位意涵"] || "",
      "宮位星座": r["宮位星座"],
      "宮中行星": planets && planets !== "無" ? planets : "-"
    };
  });
  fillTable("#houses_rows",
    ["宮位","宮名","宮位意涵","宮位星座","宮中行星"],
    houses
  );

  // AI 建議與致謝（Markdown）
  const md = (txt)=> window.marked ? marked.parse(txt||"") : (txt||"");
  const adv = document.getElementById("ai_advice");
  const cre = document.getElementById("credits");
  if (adv) adv.innerHTML = md(data.ai_advice_md || "（未啟用 AI 或無內容）");
  if (cre) cre.innerHTML = md(data.credits_md || "");

  // 行星位置
  const positionsView = buildPositionsView(data);
  fillTable("#positions_rows",
    ["Symbol","行星","位置","落宮","守護宮","黃道狀態"],
    positionsView
  );

  drawAstroChart(data);
}

// —— 事件與啟動 —— //
$("#calc").addEventListener("click", fetchChart);
initSelects();
fetchChart().catch(console.error);
