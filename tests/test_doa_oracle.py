import unittest
import numpy as np
from specaoa.covariance import fuse_covariances,sample_covariance
from specaoa.crb import aoa_crb_rad2
from specaoa.doa import esprit_single_source,music_single_source,predicted_mismatch_angle_deg,ula_steering_vector
from specaoa.simulation import C_M_PER_S,SimulationConfig,simulate_single_source

class OracleDoaTests(unittest.TestCase):
 def setUp(self): self.d=C_M_PER_S/(2*1.3e9);self.grid=np.arange(-60,60.01,.05)
 def test_noiseless_music_and_esprit(self):
  for f,a in ((.3e9,-45.),(.8e9,10.),(1.3e9,50.)):
   y=simulate_single_source(SimulationConfig(f,a,[32e6],[128],element_spacing_m=self.d));r=sample_covariance(y.observations[0].samples)
   self.assertLessEqual(abs(music_single_source(r,f,self.grid,self.d).interpolated_angle_deg-a),.1)
   self.assertLessEqual(abs(esprit_single_source(r,f,self.d)-a),.2)
 def test_sampling_rate_invariant_subspace(self):
  y=simulate_single_source(SimulationConfig(.8e9,30.,[20e6,200e6],[128,128],element_spacing_m=self.d));r=[sample_covariance(x.samples) for x in y.observations]
  v=[np.linalg.eigh(x)[1][:,-1] for x in r];self.assertGreater(abs(np.vdot(v[0],v[1])),1-1e-10)
 def test_frequency_mismatch_rule(self):
  f,a,assumed=.8e9,30.,.7e9;y=simulate_single_source(SimulationConfig(f,a,[32e6],[256],element_spacing_m=self.d));r=sample_covariance(y.observations[0].samples);estimate=music_single_source(r,assumed,self.grid,self.d).interpolated_angle_deg
  self.assertLess(abs(estimate-predicted_mismatch_angle_deg(f,assumed,a)),.1)
 def test_fusion_and_crb(self):
  eye=np.eye(3,dtype=complex);fused,w=fuse_covariances([eye,2*eye],[10,30],'snapshot_weighted');np.testing.assert_allclose(w,[.25,.75]);np.testing.assert_allclose(fused,fused.conj().T)
  self.assertGreater(aoa_crb_rad2(.3e9,30,8,self.d,64,0),aoa_crb_rad2(1.3e9,30,8,self.d,64,0));self.assertGreater(aoa_crb_rad2(.8e9,30,8,self.d,64,0),aoa_crb_rad2(.8e9,30,8,self.d,256,10))
