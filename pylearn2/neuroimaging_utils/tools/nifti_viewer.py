import argparse
from math import ceil

import matplotlib
matplotlib.use('Agg')
from matplotlib.patches import FancyBboxPatch
from matplotlib import pylab as plt
from matplotlib import rc

from nipy import load_image
from nipy.core.api import xyz_affine
from nipy.labs.viz import plot_map

import numpy as np
from sys import stdout
import pickle


cdict = {'red': ((0.0, 0.0, 0.0),
                 (0.25, 0.2, 0.2),
                 (0.45, 0.0, 0.0),
                 (0.5, 0.5, 0.5),
                 (0.55, 0.0, 0.0),
                 (0.75, 0.8, 0.8),
                 (1.0,  1.0, 1.0)),
         'green': ((0.0, 0.0, 1.0),
                   (0.25, 0.0, 0.0),
                   (0.45, 0.0, 0.0),
                   (0.5, 0.5, 0.5),
                   (0.55, 0.0, 0.0),
                   (0.75, 0.0, 0.0),
                   (1.0,  1.0, 1.0)),
         'blue':  ((0.0, 0.0, 1.0),
                   (0.25, 0.8, 0.8),
                   (0.45, 0.0, 0.0),
                   (0.5, 0.5, 0.5),
                   (0.55, 0.0, 0.0),
                   (0.75, 0.0, 0.0),
                   (1.0,  0.0, 0.0)),}

cmap = matplotlib.colors.LinearSegmentedColormap('my_colormap',cdict,256)

def montage(nifti, anat, roi_dict, thr=2,
            fig=None, out_file=None, feature_dict=None,
            target_stat=None, target_value=None):
    if isinstance(anat, str):
        anat = load_image(anat)
    assert nifti is not None
    assert anat is not None
    assert roi_dict is not None

    texcol = 1
    bgcol = 0
    iscale = 2
    weights = nifti.get_data(); #weights = weights / weights.std(axis=3)
    features = weights.shape[-1]

    indices = [0]        
    y = 8
    x = int(ceil(1.0 * features / y))

    font = {'size':8}
    rc('font',**font)
 
    if fig is None:
        fig = plt.figure(figsize=[iscale * y, iscale * x / 2.5])
    plt.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.99, wspace=0.1, hspace=0)

    for f in xrange(features):
        roi = roi_dict.get(f, None)
        if roi is None:
            continue
        coords = roi["top_clust"]["coords"]
        assert coords is not None

#        stdout.write("\rSaving montage: %d   " % f)
#        stdout.flush()
            
        feat = weights[:, :, :, f]
        feat = feat / feat.std()
        imax = np.max(np.absolute(feat)); imin = -imax
        imshow_args = {'vmax': imax, 'vmin': imin}
         

        # For some reason we need to do this.
        coords = ([-coords[0], -coords[1], coords[2]])

        ax = fig.add_subplot(x, y, f + 1)
        plt.axis('off')

        max_idx = np.unravel_index(np.argmax(feat), feat.shape)

        try: plot_map(feat,
                      xyz_affine(nifti),
                      anat=anat.get_data(),
                      anat_affine=xyz_affine(anat), 
                      threshold=thr,
                      figure=fig,
                      axes=ax,
                      cut_coords=coords,
                      annotate=False,
                      cmap=cmap, 
                      draw_cross=False,
                      **imshow_args)            
        except Exception as e:
            print e

        plt.text(0.05, 0.8, str(f),
                 transform=ax.transAxes,
                 horizontalalignment='center',
                 color=(texcol,texcol,texcol))
        pos = [(0.05, 0.05), (0.4, 0.05), (0.8, 0.05)]
        colors = ["purple", "yellow", "green"]
        if feature_dict is not None and feature_dict.get(f, None) is not None:
            d = feature_dict[f]
            for i, key in enumerate([k for k in d if k != "real_id"]):
                plt.text(pos[i][0], pos[i][1], "%s=%.2f" % (key, d[key]) ,transform=ax.transAxes,
                         horizontalalignment="left", color=colors[i])
                if key == target_stat:
                    assert target_value is not None
                    if d[key] >= target_value:
                        p_fancy = FancyBboxPatch((0.1, 0.1), 2.5 - .1, 1 - .1,
                                                 boxstyle="round,pad=0.1",
                                                 ec=(1., 0.5, 1.),
                                                 fc="none")
                        ax.add_patch(p_fancy)
                    elif d[key] <= -target_value:
                        p_fancy = FancyBboxPatch((0.1, 0.1), iscale * 2.5 - .1, iscale - .1,
                                                 boxstyle="round,pad=0.1",
                                                 ec=(0., 0.5, 0.),
                                                 fc="none")
                        ax.add_patch(p_fancy)
    
#    stdout.write("\rSaving montage: DONE\n")
    if out_file is not None:
        plt.savefig(out_file, transparent=True, facecolor=(bgcol, bgcol, bgcol))
    else:
        plt.draw()

def make_argument_parser():
    """
    Creates an ArgumentParser to read the options for this script from
    sys.argv
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("nifti", help="Nifti file to be processed.")
    parser.add_argument("--anat", default=None, help="Anat file for montage.")
    parser.add_argument("--rois", default=None, help="Pickled roi file.")
    parser.add_argument("--out", default=None, help="Output of montage.")
    parser.add_argument("--thr", default=2, help="Threshold for features.")
    return parser

def main(nifti_file, anat_file, roi_file, out_file, thr=2):
    iscale = 2
    nifti = load_image(nifti_file)
    anat = load_image(anat_file)
    roi_dict = pickle.load(open(roi_file, "rb"))
    montage(nifti, anat, roi_dict, out_file=out_file)

if __name__ == "__main__":
    parser = make_argument_parser()
    args = parser.parse_args()
    main(args.nifti, args.anat, args.rois, args.out, args.thr)

