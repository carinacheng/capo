#!/usr/bin/env python
"""Create simple 2 sigma upper limit plot.

Takes outputs from pspec_final_???.py and creates 2 sigma errorbar plots.
"""
old_analytical = False
import numpy as np
import sys
import os
import argparse
import py21cmsense as py21cm
import capo
from capo.cosmo_units import f212z
import matplotlib.pyplot as plt
from matplotlib import gridspec
import itertools

parser = argparse.ArgumentParser(
    description=('Calculate power spectra for a run '
                 'from pspec_oqe_2d.py'))
parser.add_argument('files', metavar='<FILE>', type=str, nargs='+',
                    help='List of pspec files to plot')
parser.add_argument('--plot', action='store_true',
                    help='output plot before saving')
parser.add_argument('--analytical', action='store_true',
                    help='Plot analytical noise approximation')
parser.add_argument('--noisefiles', type=str, nargs='*',
                    help='supply 21cmSense files to plot sensitivity')
parser.add_argument('--outfile', type=str, default='pspec_k3pk',
                    help='give custom output file name')
args = parser.parse_args()


zs = []
for filename in args.files:
    F = np.load(filename)
    freq = F['freq']
    zs.append(f212z(freq * 1e9))

# reverse order to make high redshift of left of plot
zs = np.unique(zs)[::-1]
Nzs = len(zs)
# define some color format sets for the plotter
# colors = ['r', 'g', 'k', 'b']
markers = ['o', ',', 'd', '^', 's', 'v']
# markers = itertools.cycle(markers)
marker_count = [0 for i in xrange(Nzs)]
figsize = (5 * (1 + Nzs)/2., 6)
# Create figure and prep subplot sizes for Delta^2
fig = plt.figure(figsize=figsize)
gs = gridspec.GridSpec(1, Nzs)
gs.update(hspace=0.0, wspace=0.2)
ax1 = [plt.subplot(gs[:, i]) for i in range(Nzs)]

# Create figure and prep subplots for P(k)
fig2 = plt.figure(figsize=figsize)
gs = gridspec.GridSpec(1, Nzs)
gs.update(hspace=0.0, wspace=0.2)
ax2 = [plt.subplot(gs[:, i]) for i in range(Nzs)]

# Create figure and prep subplot sizes for Delta^2 Noise
fig3 = plt.figure(figsize=figsize)
gs = gridspec.GridSpec(1, Nzs)
gs.update(hspace=0.0, wspace=0.2)
ax3 = [plt.subplot(gs[:, i]) for i in range(Nzs)]

# Create figure and prep subplot sizes for P(k) Noise
fig4 = plt.figure(figsize=figsize)
gs = gridspec.GridSpec(1, Nzs)
gs.update(hspace=0.0, wspace=0.2)
ax4 = [plt.subplot(gs[:, i]) for i in range(Nzs)]

if args.noisefiles:
    noise_freqs, noise_ks, noises = py21cm.load_noise_files(
        args.noisefiles, polyfit_deg=3)

    freqs = capo.pspec.z2f(zs) * 1e3
    noise_ind = np.array([np.argmin(abs(np.array(noise_freqs) - fq))
                          for fq in freqs])

    noise_freqs = np.take(noise_freqs, noise_ind).tolist()
    noise_ks = np.take(noise_ks, noise_ind, axis=0).tolist()
    noises = np.take(noises, noise_ind, axis=0).tolist()

    # Plot the Noise files on the plot
    for gs_ind in xrange(Nzs):
        ax1[gs_ind].plot(noise_ks[gs_ind], noises[gs_ind], 'c-', label='21cmSense')

        d2_n = noises[gs_ind]
        pk_n = 2*np.pi**2/(np.array(noise_ks[gs_ind])**3)*d2_n
        ax2[gs_ind].plot(noise_ks[gs_ind], pk_n, '-', color='c')
        ax2[gs_ind].plot(-np.array(noise_ks[gs_ind]), pk_n, '-', color='c', label='21cmSense')
        ax3[gs_ind].plot(noise_ks[gs_ind], noises[gs_ind], 'c-', label='21cmSense')
        ax4[gs_ind].plot(noise_ks[gs_ind], pk_n, '-', color='c')
        ax4[gs_ind].plot(-np.array(noise_ks[gs_ind]), pk_n, '-', color='c', label='21cmSense')

k_max = 0
k_par_max = 0
print 'Using these parameters for the Analytic Model:'
for filename in args.files:
    pspec_dict = np.load(filename)

    if np.max(pspec_dict['k']) > k_max:
        k_max = np.max(pspec_dict['k'])

    if np.max(np.abs(pspec_dict['kpl'])) > k_par_max:
        k_par_max = np.max(np.abs(pspec_dict['kpl']))

    # get special index for gridspec to plot all pspecs on same z value
    redshift = f212z(pspec_dict['freq'] * 1e9)
    gs_ind = int(np.where(zs == redshift)[0].item())
    marker = markers[marker_count[gs_ind]]
    marker_count[gs_ind] += 1

    pos_ind = np.where(pspec_dict['pC'] >= 0)[0]
    pos_ind_noise = np.where(pspec_dict['pCn'] >= 0)[0]
    pos_ind_fold = np.where(pspec_dict['pC_fold'] >= 0)[0]
    pos_ind_noise_fold = np.where(pspec_dict['pCn_fold'] >= 0)[0]
    neg_ind = np.where(pspec_dict['pC'] < 0)[0]
    neg_ind_noise = np.where(pspec_dict['pCn'] < 0)[0]
    neg_ind_fold = np.where(pspec_dict['pC_fold'] < 0)[0]
    neg_ind_noise_fold = np.where(pspec_dict['pCn_fold'] < 0)[0]

    ax1[gs_ind].plot(pspec_dict['k'],
                     pspec_dict['pI_fold'] + pspec_dict['pI_fold_up'], '--',
                     label='pI {0:02d}%'.format(int(pspec_dict['prob']*100)))
    #ax1[gs_ind].errorbar(pspec_dict['k'],
    #                pspec_dict['pI_fold'], pspec_dict['pI_fold_up'],
    #                label='pI {0:02d}%'.format(int(pspec_dict['prob']*100)),
    #                linestyle='',marker=marker,color='blue')
    ax1[gs_ind].errorbar(pspec_dict['k'][pos_ind_fold],
                         pspec_dict['pC_fold'][pos_ind_fold],
                         pspec_dict['pC_fold_up'][pos_ind_fold],
                         label='pC {0:02d}%'.format(int(pspec_dict['prob']*100)),
                         linestyle='', marker=marker, color='black')
    ax1[gs_ind].errorbar(pspec_dict['k'][neg_ind_fold],
                         -pspec_dict['pC_fold'][neg_ind_fold],
                         pspec_dict['pC_fold_up'][neg_ind_fold],
                         linestyle='',marker=marker, color='0.5')
    ax2[gs_ind].plot(pspec_dict['kpl'],
                     pspec_dict['pI'] + pspec_dict['pI_up'], '--',
                     label='pI {0:02d}%'.format(int(pspec_dict['prob']*100)))
    #ax2[gs_ind].errorbar(pspec_dict['kpl'],
    #                pspec_dict['pI'], pspec_dict['pI_up'],
    #                label='pI {0:02d}%'.format(int(pspec_dict['prob']*100)),
    #                linestyle='',marker=marker,color='blue')
    ax2[gs_ind].errorbar(pspec_dict['kpl'][pos_ind], pspec_dict['pC'][pos_ind],
                         pspec_dict['pC_up'][pos_ind],
                         label='pC {0:02d}%'.format(int(pspec_dict['prob']*100)),
                         linestyle='', marker=marker, color='black')
    ax2[gs_ind].errorbar(pspec_dict['kpl'][neg_ind], -pspec_dict['pC'][neg_ind],
                         pspec_dict['pC_up'][neg_ind],
                         linestyle='', marker=marker, color='0.5')
    ax3[gs_ind].plot(pspec_dict['k'],
                     pspec_dict['pIn_fold'] + pspec_dict['pIn_fold_up'], '--',
                     label='pIn {0:02d}%'.format(int(pspec_dict['prob']*100)))
    #ax3[gs_ind].errorbar(pspec_dict['k'],
    #                    pspec_dict['pIn_fold'], pspec_dict['pIn_fold_up'],
    #                    label='pIn {0:02d}%'.format(int(pspec_dict['prob']*100)),
    #                    linestyle='', marker=marker, color='blue')
    ax3[gs_ind].errorbar(pspec_dict['k'][pos_ind_noise_fold],
                         pspec_dict['pCn_fold'][pos_ind_noise_fold],
                         pspec_dict['pCn_fold_up'][pos_ind_noise_fold],
                         label='pCn {0:02d}%'.format(int(pspec_dict['prob']*100)),
                         linestyle='', marker=marker, color='black')
    ax3[gs_ind].errorbar(pspec_dict['k'][neg_ind_noise_fold],
                         -pspec_dict['pCn_fold'][neg_ind_noise_fold],
                         pspec_dict['pCn_fold_up'][neg_ind_noise_fold],
                         linestyle='', marker=marker, color='0.5')
    ax4[gs_ind].plot(pspec_dict['kpl'],
                     pspec_dict['pIn'] + pspec_dict['pIn_up'], '--',
                     label='pIn {0:02d}%'.format(int(pspec_dict['prob']*100)))
    #ax4[gs_ind].errorbar(pspec_dict['kpl'],
    #                pspec_dict['pIn'], pspec_dict['pIn_up'],
    #                label='pIn {0:02d}%'.format(int(pspec_dict['prob']*100)),
    #                linestyle='', marker=marker, color='blue')
    ax4[gs_ind].errorbar(pspec_dict['kpl'][pos_ind_noise],
                         pspec_dict['pCn'][pos_ind_noise],
                         pspec_dict['pCn_up'][pos_ind_noise],
                         label='pCn {0:02d}%'.format(int(pspec_dict['prob']*100)),
                         linestyle='', marker=marker, color='black')
    ax4[gs_ind].errorbar(pspec_dict['kpl'][neg_ind_noise],
                         -pspec_dict['pCn'][neg_ind_noise],
                         pspec_dict['pCn_up'][neg_ind_noise],
                         linestyle='', marker=marker, color='0.5')

    if args.analytical:
        inttime = pspec_dict['frf_inttime']
        nbls = pspec_dict['nbls_eff']
        cnt = pspec_dict['cnt_eff']
        nlsts = len(pspec_dict['lsts']) * pspec_dict['inttime']
        nlsts /= pspec_dict['frf_inttime']
        if pspec_dict['frf_inttime'] == pspec_dict['inttime']:
            omega_eff = .74**2/.32 # for capo analytical; from T1 of Parsons FRF paper
        else:
            omega_eff = .74**2/.24
        print 'Redshift:', redshift
        print '\tT_int:', inttime
        print '\tNbls:', nbls
        print '\tNdays:', cnt
        print '\tNlsts:', nlsts
        if old_analytical:
            tsys = 500e3  #mK
            nseps = 1  #number of seps used
            folding = 2 # XXX 2 for delta^2
            nmodes = (nlsts*nseps*folding)**.5
            pol = 2
            real = np.sqrt(2)
            sdf = .1/203
            freqs = pspec_dict['afreqs']
            freq = pspec_dict['freq']
            z = capo.pspec.f2z(freq)
            X2Y = capo.pspec.X2Y(z)/1e9 #h^-3 Mpc^3 / str/ Hz
            B = sdf*freqs.size
            bm = np.polyval(capo.pspec.DEFAULT_BEAM_POLY, freq) * 2.35 #correction for beam^2
            if pspec_dict['frf_inttime'] != pspec_dict['inttime']:
                bm *= 1.3 # correction factor for FRF version of omega_pp = .32/.24 = 1.3
            scalar = X2Y * bm #* B
            #error bars minimum width. Consider them flat for P(k). Factor of 2 at the end is due to folding of kpl (root(2)) and root(2) in radiometer equation.
            #pk_noise = 2*scalar*fr_correct*( (tsys)**2 / (2*inttime*pol*real*nbls*ndays*nmodes) ) #this 2-sigma curve should encompass 95% of the points
            pk_noise = 2*scalar*( (tsys)**2 / (inttime*pol*real*nbls*cnt*nmodes) ) # this 2-sigma curve should line up with pI
            # Plot analytical noise curve on plots
            ax1[gs_ind].plot(pspec_dict['k'],pk_noise*pspec_dict['k']**3/(2*np.pi**2),'g-',label='Analytical 2-sigma')
            ax2[gs_ind].axhline(pk_noise,color='g',marker='_',label='Analytical 2-sigma')
            ax3[gs_ind].plot(pspec_dict['k'],pk_noise*pspec_dict['k']**3/(2*np.pi**2),'g-',label='Analytical 2-sigma')
            ax4[gs_ind].axhline(pk_noise,color='g',marker='_',label='Analytical 2-sigma')
        else: #new capo.sensitivity
            from capo import sensitivity
            S = sensitivity.Sense()
            f = freq
            S.z = capo.pspec.f2z(f)

            #   Tsys
            #S.Tsys = 551e3  #set to match 21cmsense exactly
            #S.Tsys = 505e3 #Ali et al, at 164MHz
            S.Tsys = (200 + 180.*(f/.180)**-2.55)*1e3 #set to match noise realization
            print "Tsys = ",S.Tsys

            S.t_int = inttime
            S.Ndays = cnt  #effective number of days
            S.Nlstbins = nlsts  #either Nlsthours or Nlstbins must be set
            S.Nbls = nbls #nbls = nbls * sqrt((1-1/ngroups)/2), calculated in
            S.Npols = 2
            S.Nseps = 1
            S.Nblgroups = 1 #groups are already folded into the calculation of nbls_eff
            S.Omega_eff = omega_eff #use the FRF weighted beams listed in T1 of Parsons etal beam sculpting paper
            S.calc()
            print "capo.sensitivity Pk_noise = ",S.P_N
            k = pspec_dict['k']
            # Plot analytical noise curve on plots
            ax1[gs_ind].plot(k,S.Delta2_N(k)*2,'g-',label='Analytical 2-sigma')
            ax2[gs_ind].axhline(S.P_N*2,color='g',marker='_',label='Analytical 2-sigma')
            ax3[gs_ind].plot(k,S.Delta2_N(k)*2,'g-',label='Analytical 2-sigma')
            ax4[gs_ind].axhline(S.P_N*2,color='g',marker='_',label='Analytical 2-sigma')


# set up some parameters to make the figures pretty
for gs_ind in xrange(Nzs):
    # only set ylabel for first plot
    if gs_ind == 0:
        ax1[gs_ind].set_ylabel('$\\frac{k^{3}}{2\pi^{2}}$ $P(k)$ $[mK^{2}]$')
        ax2[gs_ind].set_ylabel('$P(k)$ $[mK^{2}(h^{-1} Mpc)^{3}]$')
        ax3[gs_ind].set_ylabel('$\\frac{k^{3}}{2\pi^{2}}$ $P(k)$ $[mK^{2}]$')
        ax4[gs_ind].set_ylabel('$P(k)$ $[mK^{2}(h^{-1} Mpc)^{3}]$')

    ax1[gs_ind].set_title('z = {0:.2f}'.format(zs[gs_ind]))
    ax1[gs_ind].set_yscale('log', nonposy='clip')
    ax1[gs_ind].set_xlabel('$k$ [$h$ Mpc$^{-1}$]')
    ax1[gs_ind].set_xlim(0, k_max * 1.01)
    ax1[gs_ind].get_shared_y_axes().join(ax1[0], ax1[gs_ind])
    ax1[gs_ind].grid(True)

    ax2[gs_ind].set_yscale('log', nonposy='clip')
    ax2[gs_ind].set_title('z = {0:.2f}'.format(zs[gs_ind]))
    ax2[gs_ind].set_xlabel('$k_{\\parallel}$ [$h$ Mpc$^{-1}$]')
    ax2[gs_ind].set_xlim(-1.01 * k_par_max, k_par_max * 1.01)
    ax2[gs_ind].get_shared_y_axes().join(ax2[0], ax2[gs_ind])
    ax2[gs_ind].grid(True)

    ax3[gs_ind].set_title('z = {0:.2f}'.format(zs[gs_ind]))
    ax3[gs_ind].set_yscale('log', nonposy='clip')
    ax3[gs_ind].set_xlabel('$k$ [$h$ Mpc$^{-1}$]')
    ax3[gs_ind].set_xlim(0, k_max * 1.01)
    ax3[gs_ind].get_shared_y_axes().join(ax3[0], ax3[gs_ind])
    ax3[gs_ind].grid(True)

    ax4[gs_ind].set_yscale('log', nonposy='clip')
    ax4[gs_ind].set_title('z = {0:.2f}'.format(zs[gs_ind]))
    ax4[gs_ind].set_xlabel('$k_{\\parallel}$ [$h$ Mpc$^{-1}$]')
    ax4[gs_ind].set_xlim(-1.01 * k_par_max, k_par_max * 1.01)
    ax4[gs_ind].get_shared_y_axes().join(ax4[0], ax4[gs_ind])
    ax4[gs_ind].grid(True)

    # if multi redshift, make shared axes invisible
    if gs_ind > 0:
        plt.setp(ax1[gs_ind].get_yticklabels(), visible=False)
        plt.setp(ax2[gs_ind].get_yticklabels(), visible=False)
        plt.setp(ax3[gs_ind].get_yticklabels(), visible=False)
        plt.setp(ax4[gs_ind].get_yticklabels(), visible=False)

ax1[0].set_ylim([1e-1, 1e12])
ax1[0].set_xlim([0.0, 0.6])
ax2[0].set_ylim([1e-1, 1e12])
ax2[0].set_xlim([-0.6, 0.6])
ax3[0].set_ylim([1e-1, 1e12])
ax3[0].set_xlim([0.0, 0.6])
ax4[0].set_ylim([1e-1, 1e12])
ax4[0].set_xlim([-0.6, 0.6])

handles, labels = ax1[-1].get_legend_handles_labels()
ax1[-1].legend(handles, labels, loc='lower right', numpoints=1)
handles, labels = ax2[-1].get_legend_handles_labels()
ax2[-1].legend(handles, labels, loc='lower right', numpoints=1)
handles, labels = ax3[-1].get_legend_handles_labels()
ax3[-1].legend(handles, labels, loc='lower right', numpoints=1)
handles, labels = ax4[-1].get_legend_handles_labels()
ax4[-1].legend(handles, labels, loc='lower right', numpoints=1)


fig.savefig(args.outfile+'.png', format='png')
fig2.savefig(args.outfile+'_pk.png', format='png')
fig3.savefig(args.outfile+'_noise.png', format='png')
fig3.savefig(args.outfile+'_pk_noise.png', format='png')

if args.plot:
    plt.show()