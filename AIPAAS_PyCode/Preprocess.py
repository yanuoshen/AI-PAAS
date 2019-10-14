# -*- coding: utf-8 -*-
"""
AI-PAAS ,Ryerson Univesity

Created on Tue Sep 17 12:19:06 2019

@author: 
    Tejas Janardhan
    AI-PAAS Phd Candidate

"""

# =============================================================================
# # Always use s_rep>1 to give non similar train_out values
# =============================================================================

#Libraries       Thia module needs optimising , use iterators

import scipy.signal      as scipy_sig
import numpy             as np

class cMAPSS:
  
    @classmethod
    def savgol(cls, signal):
    
        smooth_sig = scipy_sig.savgol_filter(signal, 
                                             cls.win_len, 
                                             cls.p_order, 
                                             mode='nearest')
        return smooth_sig

    @classmethod
    def config_params(cls, win_len, p_order, threshold, s_rep, s_len):
        
        cls.win_len   = win_len
        cls.p_order   = p_order
        cls.threshold = threshold
        cls.s_rep     = s_rep
        cls.s_len     = s_len
    

    @classmethod
    def basic_preprocess(cls, input_data):
        
        cls.no_engines  = input_data.iloc[-1,0]
        cls.max_cycles  = input_data['Cycles'].max()
        engine_id       = input_data.iloc[:,0]
        input_data      = input_data.iloc[:,2:]

        data_variance   = input_data.var()
        input_data     = input_data.loc[:, data_variance > cls.threshold]
    
        for i in range(1,cls.no_engines+1):
        
            input_data.loc[engine_id == i,:] = input_data.loc[engine_id == i,:].apply(cls.savgol)
            
        #Normalising after data has been filtered
        input_data = input_data.apply(lambda x: (x-x.mean())/(x.std()))
        
        return engine_id, input_data
    
    @classmethod
    def train_preprocess(cls, train_data):
        
        engine_id, train_data = cls.basic_preprocess(train_data)
        
        #preparing data for the LSTM
        cls.train_in  = np.full((cls.no_engines*cls.s_rep, 
                                 cls.max_cycles, 
                                 train_data.shape[1]),
                                 1000.0)
            
        cls.train_out = np.full((cls.no_engines*cls.s_rep),1e-2)
        
        for i in range(0, cls.no_engines*cls.s_rep, cls.s_rep):
            
            e_id      = i/cls.s_rep + 1
            cycle_len = train_data.loc[engine_id == e_id, :].shape[0]
            temp      = train_data.loc[engine_id == e_id, :]
            temp      = temp.to_numpy()
            cls.train_in[i, :cycle_len, :] = temp
            
            for j in range(1, cls.s_rep):
                
                cls.train_in[j+i, :cycle_len-cls.s_len*j, :] = temp[:-cls.s_len*j,:]
                cls.train_out[j+i] = cls.s_len*j
                
    @classmethod
    def test_preprocess(cls, test_data):
        
        engine_id, test_data = cls.basic_preprocess(test_data)
        
        #preparing data for the LSTM
        cls.test_in  = np.full((cls.no_engines, 
                                 cls.max_cycles, 
                                 test_data.shape[1]),
                                 1000.0)
            
        for i in range(cls.no_engines):
            
            cycle_len = test_data.loc[engine_id == i+1, :].shape[0]
            temp      = test_data.loc[engine_id == i+1, :]
            temp      = temp.to_numpy()
            cls.test_in[i, :cycle_len, :] = temp
            
    win_len   = 21
    p_order   = 3
    threshold = 1e-5
    s_rep     = 2    #Stagered Repetition
    s_len     = 10   #Unit - Cycles



if __name__ == '__main__':
    
    from Input import cMAPSS as ci
    
    ci.get_data(1)
    
    cMAPSS.test_preprocess(ci.Test_input)
