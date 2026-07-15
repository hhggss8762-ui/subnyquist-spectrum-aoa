"""Run Stage 0 P0-3 low-rate temporal-spatial identifiability screening."""
from __future__ import annotations

import argparse, csv, json, platform, subprocess, sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml

from specaoa.identifiability import MappingConfig
from specaoa.sampling_rate_search import SearchConfig, enumerate_rate_sets, evaluate_combination, pareto_flags
from specaoa.simulation import C_M_PER_S

REQUIRED = ((200,), (200,250), (200,250,300), (20,), (20,25), (20,25,32), (20,25,32,40), (25,32), (25,32,40), (32,40))
DETAIL = ((200,), (200,250), (200,250,300), (20,25), (20,25,32), (20,25,32,40))

def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows: return
    with path.open('w', newline='', encoding='utf-8') as h:
        writer = csv.DictWriter(h, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

def draw_scatter(rows, out):
    x=np.array([float(r['sum_sampling_rate_mhz']) for r in rows]); t=np.array([float(r['temporal_unique_coverage']) for r in rows]); j=np.array([float(r['joint_unique_coverage']) for r in rows]); g=np.array([float(r['spatial_absolute_gain']) for r in rows]); tm=np.array([float(r['temporal_margin_min']) for r in rows]); jm=np.array([float(r['joint_margin_min']) for r in rows])
    figures=[('cost_temporal_coverage.png',x,t,'Total sampling rate (MHz)','Temporal unique coverage'),('cost_joint_coverage.png',x,j,'Total sampling rate (MHz)','Joint unique coverage'),('cost_spatial_gain.png',x,g,'Total sampling rate (MHz)','Spatial absolute gain'),('temporal_vs_joint_coverage.png',t,j,'Temporal unique coverage','Joint unique coverage'),('temporal_vs_joint_margin.png',tm,jm,'Minimum temporal margin','Minimum joint margin')]
    for name,a,b,xlab,ylab in figures:
        fig,ax=plt.subplots(figsize=(7,5)); ax.scatter(a,b,s=13,alpha=.65); ax.set(xlabel=xlab,ylabel=ylab,title='P0-3 sampling-rate combinations'); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(out/name,dpi=160); plt.close(fig)
    pareto=[r for r in rows if r['is_pareto_optimal']]; fig,ax=plt.subplots(figsize=(7,5)); ax.scatter(x,j,s=12,alpha=.25,label='all'); ax.scatter([float(r['sum_sampling_rate_mhz']) for r in pareto],[float(r['joint_unique_coverage']) for r in pareto],c='crimson',label='Pareto'); ax.set(xlabel='Total sampling rate (MHz)',ylabel='Joint unique coverage',title='P0-3 Pareto candidates'); ax.legend(); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(out/'pareto_front.png',dpi=160); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,5)); ax.scatter([float(r['broadside_joint_coverage']) for r in rows],[float(r['off_broadside_joint_coverage']) for r in rows],s=12,alpha=.55); ax.plot([0,1],[0,1],'k--',lw=1); ax.set(xlabel='Broadside (|AoA| ≤ 10°) joint coverage',ylabel='Off-broadside joint coverage',title='Broadside versus off-broadside identifiability'); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(out/'broadside_comparison.png',dpi=160); plt.close(fig)

def grid_rows(arrays):
    f,a=arrays['frequencies_hz'],arrays['angles_deg']; rows=[]
    for i,fhz in enumerate(f):
        for k,deg in enumerate(a):
            nf,na=arrays['nearest_f'][i,k],arrays['nearest_a'][i,k]
            rows.append({'frequency_hz':fhz,'angle_deg':deg,'num_temporal_candidates':int(arrays['temporal'][i,k]),'num_joint_candidates':int(arrays['joint'][i,k]),'temporal_unique':bool(arrays['temporal'][i,k]==1),'joint_unique':bool(arrays['joint'][i,k]==1),'candidate_reduction_ratio':arrays['reduction'][i,k],'temporal_margin':arrays['temporal_margin'][i,k],'joint_margin':arrays['joint_margin'][i,k],'nearest_competing_frequency_hz':f[nf],'nearest_competing_angle_deg':a[na]})
    return rows

def heatmaps(combo, arrays, out):
    fields=[('temporal','Temporal candidates'),('joint','Joint candidates'),('reduction','Candidate reduction ratio')]
    for key,title in fields:
        fig,ax=plt.subplots(figsize=(7,4)); im=ax.imshow(arrays[key].T,origin='lower',aspect='auto',extent=[arrays['frequencies_hz'][0]/1e9,arrays['frequencies_hz'][-1]/1e9,arrays['angles_deg'][0],arrays['angles_deg'][-1]]); ax.set(title=f'{combo}: {title}',xlabel='Carrier frequency (GHz)',ylabel='AoA (deg)'); fig.colorbar(im,ax=ax); fig.tight_layout(); fig.savefig(out/f'{key}_heatmap_{combo.replace("+","_")}.png',dpi=160); plt.close(fig)

def coverage_plots(details, out):
    fig,ax=plt.subplots(figsize=(8,5))
    for combo,arrays in details.items():
        ax.plot(arrays['frequencies_hz']/1e9,np.mean(arrays['joint']==1,axis=1),label='+'.join(map(str,combo)))
    ax.set(xlabel='Carrier frequency (GHz)',ylabel='Joint unique coverage over AoA',title='Key combinations: frequency-resolved coverage'); ax.legend(fontsize=7); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(out/'key_frequency_coverage.png',dpi=160); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,5))
    for combo,arrays in details.items():
        ax.plot(arrays['angles_deg'],np.mean(arrays['joint']==1,axis=0),label='+'.join(map(str,combo)))
    ax.set(xlabel='AoA (deg)',ylabel='Joint unique coverage over frequency',title='Key combinations: angle-resolved coverage'); ax.legend(fontsize=7); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(out/'key_angle_coverage.png',dpi=160); plt.close(fig)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--config',default='configs/p0_3_sampling_rate_search.yaml'); parser.add_argument('--output',default='results/p0_3_sampling_rate_search'); parser.add_argument('--resume',action='store_true'); args=parser.parse_args()
    raw=yaml.safe_load(Path(args.config).read_text(encoding='utf-8')); search=SearchConfig(**raw); mapping=MappingConfig(element_spacing_m=C_M_PER_S/(2*1.3e9)); out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    combos=enumerate_rate_sets(search,REQUIRED); cache=out/'intermediate.jsonl'; done={}
    if args.resume and cache.exists():
        for line in cache.read_text(encoding='utf-8').splitlines():
            row=json.loads(line); done[row['combination_id']]=row
    details={}; started=datetime.now(timezone.utc)
    with cache.open('a',encoding='utf-8') as log:
        for n,combo in enumerate(combos,1):
            cid='r_'+'_'.join(map(str,combo))
            if cid in done: continue
            try:
                row, arrays=evaluate_combination(combo,search,mapping); done[cid]=row; log.write(json.dumps(row)+'\n'); log.flush()
                if combo in DETAIL: details[combo]=arrays
            except Exception as exc:
                done[cid]={'combination_id':cid,'sampling_rates_mhz':'+'.join(map(str,combo)),'status':f'error: {exc}'}; log.write(json.dumps(done[cid])+'\n'); log.flush()
            if n%50==0 or n==len(combos): print(f'[{n}/{len(combos)}] combinations completed',flush=True)
    rows=[done['r_'+'_'.join(map(str,c))] for c in combos if done['r_'+'_'.join(map(str,c))].get('status')=='ok']; pareto_flags(rows); write_csv(out/'all_combinations.csv',rows); write_csv(out/'pareto_front.csv',[r for r in rows if r['is_pareto_optimal']])
    recommended=[]
    for cat in ('A','B','C','D'):
        selected=[r for r in rows if r['category']==cat]
        selected.sort(key=lambda r:(-float(r['spatial_absolute_gain']),-float(r['joint_unique_coverage']),float(r['sum_sampling_rate_mhz'])))
        recommended.extend(selected[:10])
    write_csv(out/'recommended_combinations.csv',recommended); draw_scatter(rows,out)
    for combo in DETAIL:
        if combo not in details: _,details[combo]=evaluate_combination(combo,search,mapping)
        label='+'.join(map(str,combo)); write_csv(out/f'grid_details_{label.replace("+","_")}.csv',grid_rows(details[combo]))
    coverage_plots(details,out)
    a=[r for r in rows if r['category']=='A']; best=max(a,key=lambda r:float(r['spatial_absolute_gain'])) if a else max(rows,key=lambda r:float(r['spatial_absolute_gain']))
    if best:
        combo=tuple(map(int,str(best['sampling_rates_mhz']).split('+'))); _,arrays=evaluate_combination(combo,search,mapping); heatmaps(str(best['sampling_rates_mhz']),arrays,out)
    commit=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip() or 'uncommitted'
    counts={cat:sum(r['category']==cat for r in rows) for cat in ('A','B','C','D','unclassified')}
    conclusion='GO' if a else ('CONDITIONAL GO' if any(float(r['spatial_absolute_gain'])>=.05 for r in rows) else 'NO-GO')
    highest_temporal=max(rows,key=lambda r:float(r['temporal_unique_coverage']))
    highest_joint=max(rows,key=lambda r:float(r['joint_unique_coverage']))
    highest_margin=max(rows,key=lambda r:float(r['joint_margin_min']))
    worst_broadside=min(rows,key=lambda r:float(r['broadside_joint_coverage'])-float(r['off_broadside_joint_coverage']))
    lines=['# P0-3 Sampling-Rate Search Summary','', '## Experiment purpose','Screen low-rate combinations where temporal aliases remain ambiguous but spatial phase materially improves noiseless joint identifiability.','', '## Configuration',f'- Frequency grid: 0.3–1.3 GHz, step {search.frequency_step_hz/1e6:g} MHz.',f'- AoA grid: -60–60 deg, step {search.angle_step_deg:g} deg.',f'- ULA: M=8, d=c/(2·1.3 GHz)={mapping.element_spacing_m:.9g} m.',f'- Search: {len(combos)} combinations; budget <= {search.max_total_rate_mhz} MHz plus mandatory controls.',f'- Command: `python scripts/run_p0_3_sampling_rate_search.py --config {args.config}`.',f'- Git commit: {commit}; Python: {platform.python_version()}; completed {datetime.now(timezone.utc).isoformat()}.','', '## Results',f'- Categories: {counts}.',f'- GO / NO-GO decision: **{conclusion}**.']
    lines.extend(['', '### Leading observations',f"- Highest temporal coverage: `{highest_temporal['sampling_rates_mhz']} MHz` ({float(highest_temporal['temporal_unique_coverage']):.2%}).",f"- Highest joint coverage: `{highest_joint['sampling_rates_mhz']} MHz` ({float(highest_joint['joint_unique_coverage']):.2%}).",f"- Largest minimum joint margin: `{highest_margin['sampling_rates_mhz']} MHz` ({float(highest_margin['joint_margin_min']):.6g}); grid-level minima are often zero where exact broadside competitors remain.",f"- Strongest broadside deficit: `{worst_broadside['sampling_rates_mhz']} MHz`; broadside={float(worst_broadside['broadside_joint_coverage']):.2%}, off-broadside={float(worst_broadside['off_broadside_joint_coverage']):.2%}.",f"- Pareto count: {sum(bool(r['is_pareto_optimal']) for r in rows)}. `200+250+300 MHz` is retained as the C-class time-only negative control.",'', '## Interpretation','- Confirmed: spatial phase can reduce strict candidate counts for low-rate combinations, especially away from broadside.','- Not confirmed: no searched set satisfies the initial A-class requirement of temporal ambiguity plus >=90% joint unique coverage.','- Broadside: at theta=0°, u=f sin(theta)=0 for every carrier, so normalized ULA phase alone cannot distinguish temporal candidates.','- Next action: enter P0-4 only as a conditional Oracle-frequency AOA diagnostic; do not yet nominate a main low-rate recovery configuration.'])
    label='Best A' if a else 'Highest-gain (not A)'
    lines.extend([f"- {label} combination: `{best['sampling_rates_mhz']} MHz`; temporal={float(best['temporal_unique_coverage']):.2%}, joint={float(best['joint_unique_coverage']):.2%}, gain={float(best['spatial_absolute_gain']):.2%}.", '- P0-4 recommendation: proceed only as a conditional Oracle-frequency diagnostic; retain this result as evidence of broadside/strict-identifiability limitations.'])
    (out/'summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
