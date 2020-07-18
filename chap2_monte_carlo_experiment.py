# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from scipy.linalg import block_diag
from sklearn.covariance import LedoitWolf

import marcenko_pastur_pdf as mp

# Code snippet 2.7
#Generate a block-diagnoal covariance matrix and a vector of means
def formBlockMatrix(nBlocks, bSize, bCorr):
    block = np.ones( (bSize, bSize))*bCorr
    block[range(bSize), range(bSize)] = 1 #diagonal is 1
    corr = block_diag(*([block]*nBlocks))
    return corr
    
def formTrueMatrix(nBlocks, bSize, bCorr):
    corr0 = formBlockMatrix(nBlocks, bSize, bCorr)
    corr0 = pd.DataFrame(corr0)
    cols = corr0.columns.tolist()
    np.random.shuffle(cols)
    corr0 = corr0[cols].loc[cols].copy(deep=True)
    std0 = np.random.uniform(.05, .2, corr0.shape[0])
    cov0 = corr2cov(corr0, std0)
    mu0 = np.random.normal(std0, std0, cov0.shape[0]).reshape(-1,1)
    return mu0, cov0
    
def corr2cov(corr, std):
    cov = corr * np.outer(std, std)
    return cov
    
# Code snippet 2.8
# generating the empirical covariance matrix
def simCovMu(mu0, cov0, nObs, shrink=False):
    x = np.random.multivariate_normal(mu0.flatten(), cov0, size = nObs)
    #print(x.shape)
    mu1 = x.mean(axis = 0).reshape(-1,1) #calc mean of columns of rand matrix
    #print(mu1.shape)
    if shrink: cov1 = LedoitWolf().fit(x).covariance_
    else: cov1 = np.cov(x, rowvar=0)
    return mu1, cov1

# code snippet 2.9 
# Denoising of the empirical covariance matrix
# by constant residual eigenvalue method
def deNoiseCov(cov0, q, bWidth):
    corr0 = mp.cov2corr(cov0)
    eVal0, eVec0 = mp.getPCA(corr0)
    eMax0, var0 = mp.findMaxEval(np.diag(eVal0), q, bWidth)
    nFacts0 = eVal0.shape[0]-np.diag(eVal0)[::-1].searchsorted(eMax0)
    corr1 = mp.denoisedCorr(eVal0, eVec0, nFacts0) #denoising by constant residual eigenvalue method
    cov1 = corr2cov(corr1, np.diag(cov0)**.5)
    return cov1
    
# code snippet 2.10
# Derive minimum-variance-portfolio 
def optPort(cov, mu = None):
    inv = np.linalg.inv(cov)
    ones = np.ones(shape = (inv.shape[0], 1)) # column vector 1's
    if mu is None: 
        mu = ones
    w = np.dot(inv, mu)
    w /= np.dot(ones.T, w) # def: w = w / sum(w)
    return w
    
    
if __name__ == '__main__':
nBlocks, bSize, bCorr = 2, 2, .5
np.random.seed(0)
mu0, cov0 = formTrueMatrix(nBlocks, bSize, bCorr)

# code snippet 2.10
nObs, nTrials, bWidth, shrink, minVarPortf = 5, 5, .01, False, True
w1 = pd.DataFrame(columns = range(cov0.shape[0]), index = range(nTrials), dtype=float)

w1_d = w1.copy(deep=True)
np.random.seed(0)
for i in range(nTrials):
    mu1, cov1 = simCovMu(mu0, cov0, nObs, shrink = shrink)
    if minVarPortf: mu1 = None
    cov1_d = deNoiseCov(cov1, nObs*1./cov1.shape[1], bWidth)
    w1.loc[i] = optPort(cov1, mu1).flatten()
    w1_d.loc[i] = optPort(cov1_d, mu1).flatten()
        
    #code snippet 2.11
w0 = optPort(cov0, None if minVarPortf else mu0) # w0 true percentage asset allocation
w0 = np.repeat(w0.T, w1.shape[0], axis=0) #???
rmsd = np.mean((w1-w0).values.flatten()**2)**.5     #RMSE not denoised
rmsd_d = np.mean((w1_d-w0).values.flatten()**2)**.5 #RMSE denoised
print rmsd, rmsd_d
    