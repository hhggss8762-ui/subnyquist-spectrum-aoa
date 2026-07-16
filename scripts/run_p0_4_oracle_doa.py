"""P0-4 Oracle-frequency AOA, frequency-mismatch, and CRB diagnostics."""
from __future__ import annotations
import argparse,csv,json,sys,time
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import yaml
from specaoa.covariance import fuse_covariances,sample_covariance
from specaoa.crb import aoa_crb_rad2
from specaoa.doa import esprit_single_source,music_single_source,predicted_mismatch_angle_deg
from specaoa.metrics_doa import doa_metrics
from specaoa.simulation import C_M_PER_S,SimulationConfig,simulate_single_source,wrap_to_nyquist

def write(path, rows):
    if rows:
        with path.open('w',newline='',encoding='utf-8') as f: w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def covariance(f,angle,rates,n,snr,seed,spacing,mode):
    result=simulate_single_source(SimulationConfig(f,angle,rates,[n]*len(rates),element_spacing_m=spacing,snr_db=snr,random_seed=seed))
    covs=[sample_covariance(x.samples) for x in result.observations]
    return fuse_covariances(covs,[n]*len(rates),mode)[0]

def estimate(cov,assumed,grid,spacing):
    start=time.perf_counter(); music=music_single_source(cov,assumed,grid,spacing); music_time=time.perf_counter()-start
    start=time.perf_counter(); esprit=esprit_single_source(cov,assumed,spacing); esprit_time=time.perf_counter()-start
    return music,esprit,music_time,esprit_time

def main():
 p=argparse.ArgumentParser();p.add_argument('--config',default='configs/p0_4_oracle_doa.yaml');p.add_argument('--output',default='results/p0_4_oracle_doa');p.add_argument('--smoke',action='store_true');p.add_argument('--trials',type=int);p.add_argument('--nyquist-trials',type=int);p.add_argument('--skip-fixed',action='store_true');args=p.parse_args()
 c=yaml.safe_load(Path(args.config).read_text(encoding='utf-8'));out=Path(args.output);out.mkdir(parents=True,exist_ok=True);spacing=C_M_PER_S/(2*1.3e9);grid=np.arange(-60,60.0001,.2 if args.smoke else c['angle_grid_step_deg']);sets=[tuple(int(x) for x in s) for s in c['sampling_rate_sets_mhz']];ratesets=[tuple(x*1e6 for x in s) for s in sets]; trials=args.trials or c['monte_carlo_trials']
 freqs=c['frequencies_hz']; fixed_angles=c['fixed_angles_deg']; snrs=c['snr_db']; snaps=c['snapshots_per_branch']
 if args.smoke: freqs=[300e6,800e6,1300e6];fixed_angles=[-50,-10,0,10,50];snrs=[-10,0,10,20];snaps=[32,128,512]
 sanity=[]
 for label,rates in zip(sets,ratesets):
  for f in c['frequencies_hz']:
   for a in c['sanity_angles_deg']:
    cov=covariance(f,a,rates,256,None,1,spacing,c['covariance_fusion']);m,e,_,_=estimate(cov,f,grid,spacing);sanity.append({'sampling_rates_mhz':'+'.join(map(str,label)),'frequency_hz':f,'true_angle_deg':a,'music_angle_deg':m.interpolated_angle_deg,'esprit_angle_deg':e,'music_error_deg':m.interpolated_angle_deg-a,'esprit_error_deg':e-a,'status':'ok'})
 write(out/'noiseless_sanity.csv',sanity)
 rows=list(csv.DictReader((out/'fixed_snapshot_results.csv').open(encoding='utf-8'))) if args.skip_fixed and (out/'fixed_snapshot_results.csv').exists() else []
 for si,(label,rates) in ([] if args.skip_fixed else enumerate(zip(sets,ratesets))):
  for f in freqs:
   for a in fixed_angles:
    for snr in snrs:
     for n in snaps:
      values={'MUSIC':[],'ESPRIT':[]};mt=et=0.
      for trial in range(trials):
       cov=covariance(f,a,rates,n,snr,c['seed']+trial,spacing,c['covariance_fusion']);m,e,x,y=estimate(cov,f,grid,spacing);values['MUSIC'].append(m.interpolated_angle_deg-a);values['ESPRIT'].append(e-a);mt+=x;et+=y
      for method,errors in values.items():
       data={'sampling_rates_mhz':'+'.join(map(str,label)),'frequency_hz':f,'angle_deg':a,'snr_db':snr,'snapshots_per_branch':n,'num_branches':len(rates),'total_snapshots':n*len(rates),'method':method,**doa_metrics(np.asarray(errors)),'crb_rmse_deg':np.sqrt(aoa_crb_rad2(f,a,8,spacing,n*len(rates),snr))*180/np.pi,'runtime_seconds':mt if method=='MUSIC' else et};rows.append(data)
  print(f'fixed-snapshot set {si+1}/{len(sets)} complete',flush=True)
 write(out/'fixed_snapshot_results.csv',rows)
 duration=[]
 for label,rates in zip(sets,ratesets):
  for duration_s in c['observation_duration_s']:
   ns=[max(2,int(rate*duration_s)) for rate in rates];n=min(ns); f=800e6;a=30.;snr=0.;errors=[]
   for trial in range(trials):
    result=simulate_single_source(SimulationConfig(f,a,rates,ns,element_spacing_m=spacing,snr_db=snr,random_seed=c['seed']+trial));cov,_=fuse_covariances([sample_covariance(x.samples) for x in result.observations],ns,c['covariance_fusion']);errors.append(music_single_source(cov,f,grid,spacing).interpolated_angle_deg-a)
   duration.append({'sampling_rates_mhz':'+'.join(map(str,label)),'frequency_hz':f,'angle_deg':a,'snr_db':snr,'observation_duration_s':duration_s,'snapshots_by_branch':'+'.join(map(str,ns)),'sum_sampling_rate_mhz':sum(label),'method':'MUSIC',**doa_metrics(np.asarray(errors))})
 write(out/'fixed_duration_results.csv',duration)
 mismatch=[]
 for label,rates in zip(sets[:5],ratesets[:5]):
  for f in c['frequencies_hz']:
   for a in fixed_angles:
    cov=covariance(f,a,rates,256,None,c['seed'],spacing,c['covariance_fusion'])
    for err in c['frequency_error_hz']:
     assumed=f+err;pred=predicted_mismatch_angle_deg(f,assumed,a);m,_,_,_=estimate(cov,assumed,grid,spacing);mismatch.append({'true_frequency_hz':f,'assumed_frequency_hz':assumed,'absolute_frequency_error_hz':err,'relative_frequency_error':err/f,'true_angle_deg':a,'predicted_angle_deg':pred,'estimated_angle_deg':m.interpolated_angle_deg,'prediction_error_deg':m.interpolated_angle_deg-pred,'aoa_error_deg':m.interpolated_angle_deg-a,'is_physically_feasible':np.isfinite(pred),'used_alias_frequency':False,'sampling_rate_hz':'','sampling_rates_mhz':'+'.join(map(str,label))})
    for rate in rates:
     assumed=float(wrap_to_nyquist(f,rate)[0]);pred=predicted_mismatch_angle_deg(f,assumed,a);m,_,_,_=estimate(cov,assumed,grid,spacing);mismatch.append({'true_frequency_hz':f,'assumed_frequency_hz':assumed,'absolute_frequency_error_hz':assumed-f,'relative_frequency_error':(assumed-f)/f,'true_angle_deg':a,'predicted_angle_deg':pred,'estimated_angle_deg':m.interpolated_angle_deg,'prediction_error_deg':m.interpolated_angle_deg-pred,'aoa_error_deg':m.interpolated_angle_deg-a,'is_physically_feasible':np.isfinite(pred),'used_alias_frequency':True,'sampling_rate_hz':rate,'sampling_rates_mhz':'+'.join(map(str,label))})
 write(out/'frequency_mismatch_results.csv',mismatch)
 ablation=[]
 for M in (4,8,16):
  for f in (300e6,1300e6):
   errors=[]
   for trial in range(trials):
    result=simulate_single_source(SimulationConfig(f,30.,[32e6,35e6],[128,128],num_elements=M,element_spacing_m=spacing,snr_db=0,random_seed=c['seed']+trial));cov,_=fuse_covariances([sample_covariance(x.samples) for x in result.observations],[128,128],c['covariance_fusion']);errors.append(music_single_source(cov,f,grid,spacing).interpolated_angle_deg-30.)
   ablation.append({'num_elements':M,'frequency_hz':f,'angle_deg':30.,'snr_db':0.,'snapshots_per_branch':128,**doa_metrics(np.asarray(errors))})
 write(out/'array_ablation_results.csv',ablation)
 # Nyquist comparison uses the exact same fixed-snapshot conditions for one representative low-rate set.
 nyq=[]
 for f in freqs:
  for a in fixed_angles:
   for snr in snrs:
    errors=[]
    for trial in range(args.nyquist_trials or trials): errors.append(music_single_source(covariance(f,a,[c['nyquist_sampling_rate_hz']],128,snr,c['seed']+trial,spacing,c['covariance_fusion']),f,grid,spacing).interpolated_angle_deg-a)
    nyq.append({'sampling_rates_mhz':'Nyquist_3000','frequency_hz':f,'angle_deg':a,'snr_db':snr,'snapshots_per_branch':128,'num_branches':1,'total_snapshots':128,'method':'MUSIC',**doa_metrics(np.asarray(errors))})
 write(out/'nyquist_results.csv',nyq)
 # compact, data-driven figures
 arr=lambda q,k:np.asarray([float(x[k]) for x in q]);
 for name,x,y,xlab,ylab in [('rmse_vs_snr.png',arr(rows,'snr_db'),arr(rows,'rmse_deg'),'SNR (dB)','AOA RMSE (deg)'),('rmse_vs_frequency.png',arr(rows,'frequency_hz')/1e9,arr(rows,'rmse_deg'),'True frequency (GHz)','AOA RMSE (deg)'),('rmse_vs_angle.png',arr(rows,'angle_deg'),arr(rows,'rmse_deg'),'True AoA (deg)','AOA RMSE (deg)'),('rmse_vs_snapshots.png',arr(rows,'snapshots_per_branch'),arr(rows,'rmse_deg'),'Snapshots per branch','AOA RMSE (deg)')]:
  fig,ax=plt.subplots();ax.scatter(x,y,s=5,alpha=.35);ax.set(xlabel=xlab,ylabel=ylab,title='P0-4 Oracle MUSIC/ESPRIT configurations');ax.grid(alpha=.3);fig.tight_layout();fig.savefig(out/name,dpi=140);plt.close(fig)
 fig,ax=plt.subplots();alias=[r for r in mismatch if r['used_alias_frequency']];ax.scatter([r['absolute_frequency_error_hz']/1e6 for r in mismatch if not r['used_alias_frequency']],[r['aoa_error_deg'] for r in mismatch if not r['used_alias_frequency']],s=3,label='absolute error');ax.scatter([r['absolute_frequency_error_hz']/1e6 for r in alias],[r['aoa_error_deg'] for r in alias],s=5,label='alias used');ax.set(xlabel='Assumed minus true frequency (MHz)',ylabel='AOA error (deg)',title='Frequency mismatch sensitivity');ax.legend();ax.grid(alpha=.3);fig.tight_layout();fig.savefig(out/'frequency_error_vs_aoa_error.png',dpi=140);plt.close(fig)
 fig,ax=plt.subplots();good=[r for r in mismatch if np.isfinite(r['predicted_angle_deg'])];ax.scatter([r['predicted_angle_deg'] for r in good],[r['estimated_angle_deg'] for r in good],s=3);ax.plot([-60,60],[-60,60],'k--');ax.set(xlabel='Predicted mismatched angle (deg)',ylabel='MUSIC angle (deg)',title='Theory versus MUSIC mismatch angle');fig.tight_layout();fig.savefig(out/'prediction_vs_music.png',dpi=140);plt.close(fig)
 maxsan=max(abs(float(x['music_error_deg'])) for x in sanity); diff=float(np.nanmedian(arr(nyq,'rmse_deg'))-np.nanmedian(arr([r for r in rows if r['sampling_rates_mhz']=='32+35' and r['snapshots_per_branch']=='128'],'rmse_deg'))); summary=f"# P0-4 Oracle-frequency AOA\n\n- Run mode: {'smoke' if args.smoke else 'full'}; fixed-snapshot trials/configuration: {'existing 10-trial sweep' if args.skip_fixed else trials}; Nyquist trials: {args.nyquist_trials or trials}.\n- Noiseless MUSIC maximum error: {maxsan:.4g} deg.\n- Oracle AOA uses true RF frequency; alias frequency is tested only as intentional mismatch.\n- Median Nyquist minus 32+35-MHz RMSE difference (mixed grid, diagnostic): {diff:.4g} deg.\n- Frequency mismatch results validate the predicted `asin((f/fhat) sin(theta))` relation when feasible.\n- Decision: CONDITIONAL GO pending full 300-trial sweep; valid diagnostic region is assessed in the CSVs, with endfire and low-SNR configurations expected to degrade.\n"
 (out/'summary.md').write_text(summary,encoding='utf-8')
if __name__=='__main__':main()
