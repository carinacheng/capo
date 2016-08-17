#input a list of signal loss power spectra (as output by boots_to_pspsec)
#compute a loss-calibrated limit
#output as a new pspec file
from glob import glob
import argparse,os
from capo.eor_results import read_bootstraps_dcj,average_bootstraps
from capo.pspec import dk_du
from capo import cosmo_units
import numpy as np
from matplotlib.pyplot import *
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

parser = argparse.ArgumentParser(description='Calculate a limit from a range of injected pspecs')
parser.add_argument('pspec_files', metavar='pspsec.npz', type=str, nargs='+',default='.',
                    help='Directory containing injections')
args = parser.parse_args()

def G(x,mx,dx):
    return 1/(dx*np.sqrt(2*np.pi)) * np.exp(-1/2.*((x-mx)/dx)**2)
def G_mc(x_lim,dist_x,dist_sig,Ntrials=1000):
    #calculate the probability of drawing a point larger than
    # x_lim from the gaussian distribution dist_x +/- dist_sig
    #
    mc_x = np.random.normal(dist_x,dist_sig,size=Ntrials)
    return np.sum(mc_x>x_lim)/float(Ntrials)
def injpath_to_injlevel(filepath):
    injdir = os.path.split(os.path.dirname(filepath))[-1]
    return float(injdir.split('_')[-1])

def tanh(x, m, s, c = 1.0, a=1.0): return c  + a*np.tanh( (x-m)/(2*s))
def atanh(p,m,s,c,a): return 2*s*np.arctanh( (p - c )/a ) + m

#read in the bootstrapped pspecs
pspec_channels = ['pCv_fold','pCv_fold_err', #weighted data pspec
                    'pIv_fold','pIv_fold_err', #unweighted data pspec
                    'pC_fold','pC_fold_err', #weighted data+inj pspec
                    'pI_fold','pI_fold_err', #unweighted inj pspec
                    'pCv','pCv_err', #weighted data pspec
                    'pIv','pIv_err', #unweighted data pspec
                    'pC','pC_err', #weighted data+inj pspec
                    'pI','pI_err'] #unweighted inj pspec pos and neg kpls
pspecs = {}
#sort the input files. makes things easier later
injlevels = [injpath_to_injlevel(filename) for filename in args.pspec_files]
fileorder = np.argsort(injlevels)
filenames = [args.pspec_files[i] for i in fileorder]
for filename in filenames:
    print filename
    F = np.load(filename)
    for pspec_channel in pspec_channels:
        F[pspec_channel]
        try:
            pspecs[pspec_channel].append(F[pspec_channel])
        except(KeyError):
            pspecs[pspec_channel] = [F[pspec_channel]]
for pspec_channel in pspec_channels:
    pspecs[pspec_channel] = np.array(pspecs[pspec_channel])
Ninj,Nk = pspecs[pspec_channel].shape
k = F['k']
kpls= F['kpl_fold']
Nk = len(k)
freq = F['freq']
print "found injects:",Ninj
print "found k bins:",Nk

for ptype in ['pI', 'pC']:
        #limit option #1. the net probability that pC is above pcV
    probs = np.zeros((Ninj,Nk))
    for inj in xrange(Ninj):
        for k_ind in xrange(Nk):
            lossy_limit = pspecs[ptype+'v_fold'][0,k_ind]+pspecs[ptype+'v_fold_err'][0,k_ind]
            if k_ind==5:
                print "lossy_limit: ", lossy_limit
                print ptype+" lower limit",pspecs[ptype+'_fold'][inj,k_ind]-pspecs[ptype+'_fold_err'][inj,k_ind]
            probs[inj,k_ind] = G_mc(lossy_limit, #limit
                            pspecs[ptype+'_fold'][inj,k_ind],
                            pspecs[ptype+'_fold_err'][inj,k_ind])

    tanh_parms = []
    for k_ind in xrange(Nk):
        #tanh fit is VERY sensitive to initial conditions
        p0 = np.zeros(4)
        mean_ind = np.argmin( abs( probs[:,k_ind] - np.mean(probs[:,k_ind]) )  )
        p0[0] = pspecs['pI_fold'][mean_ind,k_ind] # set mean and width to central value of pspecs
        p0[1] = pspecs['pI_fold'][mean_ind,k_ind]# set mean and width to central value of pspecs
        p0[2] = .25 + np.min(probs[:,k_ind]) #offest of guess is min value + .25
        p0[3] = (np.max(probs[:,k_ind]) - np.min(probs[:,k_ind]) )*3/4.#scale is  3/4 differnce in probabilities

        parms, cov = curve_fit(tanh,
            pspecs['pI_fold'][:,k_ind],probs[:,k_ind],p0=p0,maxfev=50000)
        tanh_parms.append(parms)


        # if k_ind ==5:
        #     print "Upper limts at k={0:.4f} hMpc^-1".format(k[k_ind])
        #     print "Confidence interval", "Upper Limit"
        #     for _pl, _ul in zip(prob_limits,upper_limits[k_ind]):
        #         print " {0} \t {1:.4e}".format(_pl,_ul)

    # colormap = plt.cm.gist_ncar
    # plt.gca().set_color_cycle([colormap(i) for i in np.linspace(0, 0.9, Nk+1)])
    figure()
    for k_ind in xrange(Nk):
        plt.semilogx(pspecs['pI_fold'][:,k_ind],probs[:,k_ind],'-',label=k[k_ind])
        # plt.semilogx(pspecs['pI_fold'][:,k_ind], tanh(pspecs['pI_fold'][:,k_ind], *tanh_parms[k_ind]),'-' )
    grid()
    legend(loc='best')
    xlabel('$P_{inj}$')
    ylabel('Probability to find $P_{inj}$')
    title(ptype)
    show()
    prob_limits = [.68,.85,.9,.95,.99]
    for per in prob_limits:
        upper_limits=[]
        upper_limits.append([atanh(per,*prms) for prms in tanh_parms])
        upper_limits = np.array(upper_limits).squeeze()
        k3pk = np.tile(1e-5,(Nk))
        k3err = upper_limits * k**3/(2*np.pi**2)
        Pk = np.tile(1e-5, Nk)
        Pkerr = upper_limits

        print ptype, per
        print k3err

        np.savez('pspec_limits_k3pk_'+ptype+'_{0:02d}'.format(int(per*100))+'.npz',
            freq=freq, k=k, k3pk=k3pk, k3err=k3err,
            pk=Pk, err=Pkerr, kpl = kpls)