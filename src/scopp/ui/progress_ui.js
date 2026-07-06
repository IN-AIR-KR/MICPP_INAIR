document.querySelector('#commit').textContent=`main · ${D.commit}`;
const stats=[['테스트',`${D.tests} passed`],['Python 파일',D.pythonFiles],['유효 Cell',D.cellCount],['구현 Profile',D.profiles.length]];
document.querySelector('#stats').innerHTML=stats.map(x=>`<article class="stat"><b>${x[1]}</b><small>${x[0]}</small></article>`).join('');
const done=D.stages.filter(x=>x.status==='done').length;document.querySelector('#completion').textContent=`${done}/${D.stages.length} 완료`;
document.querySelector('#pipeline').innerHTML=D.stages.map((x,i)=>`<article class="stage ${x.status}"><span class="num">0${i+1}</span>${x.status==='done'?'<span class="check">●</span>':''}<b>${x.name}</b><small>${x.detail}</small></article>`).join('');
const max=Math.max(...D.profiles.map(x=>x.makespan));document.querySelector('#profiles').innerHTML=D.profiles.map(x=>`<div class="profile"><div><b>${x.name}</b><br><small>${x.cells.join(' / ')} cells</small></div><div class="bar"><i style="width:${x.makespan/max*100}%"></i></div><b>${x.makespan.toFixed(2)}m</b></div>`).join('');
document.querySelector('#links').innerHTML=D.links.map(x=>`<a href="${x.href}"><span>${x.name}</span><b>열기 ↗</b></a>`).join('');
document.querySelector('#next').innerHTML=D.next.map((x,i)=>`<article class="next-item"><b>0${i+1} · ${x.name}</b><p>${x.detail}</p></article>`).join('');
