"""Compute segmentation points for a collection of instrument files.

Example:
$ python scripts/segment_collection.py \
    audiofiles.csv \
    outputs \
    segment_index.csv \
    --method envelope \
    --num_cpus -1 \
    --verbose 50
"""

import argparse
from joblib import Parallel, delayed
import logging
import os
import pandas as pd
import sys

import minst.signal as S
import minst.utils as utils

logger = logging.getLogger(__name__)


def segment_one(index, audio_file, mode, output_directory):
    """Segment a single audio file.

    Parameters
    ----------
    index : str
        Index value corresponding to this audio file.

    audio_file : str
        Path to an audio file on disk.

    mode : str
        Segmentation mode to use; see minst.signal.ONSETS for more details.

    output_directory : str
        Path at which to write outputs.

    Returns
    -------
    output_file : str
        Path at which data was written.
    """
    oframe = S.segment(audio_file, mode)
    output_file = os.path.join(output_directory,
                               "{}-{}.csv".format(index, mode))
    oframe.to_csv(output_file)
    if not os.path.exists(output_file):
        raise ValueError("Did not create output! {}".format(output_file))

    return output_file


def segment_many(index, audio_files, mode, output_directory,
                 num_cpus=-1, verbose=0):
    """Segment a collection of audio files.

    Parameters
    ----------
    audio_files : array_like
        Collection of audio filepaths.

    output_directory : str
        Path at which outputs will be written.

    num_cpus : int, default=-1
        Number of CPUs to use for parallel downloads; -1 for all.

    verbose : int, default=0
        Verbosity level for parallel computation.

    Returns
    -------
    output_paths : list
        Filepaths of generated output, or None for failures.
    """
    utils.create_directory(output_directory)
    pool = Parallel(n_jobs=num_cpus, verbose=verbose)
    fx = delayed(segment_one)
    return pool(fx(idx, afile, mode, output_directory)
                for idx, afile in zip(index, audio_files))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "index_file",
        metavar="index_file", type=str,
        help="A dframe in CSV format.")
    parser.add_argument(
        "output_dir",
        metavar="output_dir", type=str,
        help="Output path for cut-point estimations.")
    parser.add_argument(
        "output_index",
        metavar="output_index", type=str,
        help="File basename for the generated output.")
    parser.add_argument(
        "--mode",
        metavar="mode", type=str, default='hll',
        help="File basename for the generated output.")
    parser.add_argument(
        "--num_cpus",
        metavar="num_cpus", type=int, default=-1,
        help="Number of CPUs to use; by default, uses all.")
    parser.add_argument(
        "--verbose",
        metavar="verbose", type=int, default=0,
        help="Number of CPUs to use; by default, uses all.")

    logging.basicConfig(level=logging.INFO)

    args = parser.parse_args()
    dframe = pd.read_json(args.index_file)
    outputs = segment_many(dframe.index.tolist(), dframe.audio_file, args.mode,
                           args.output_dir, num_cpus=args.num_cpus,
                           verbose=args.verbose)
    dframe[args.mode] = outputs
    output_file = os.path.join(args.output_dir, args.output_index)
    dframe.to_csv(output_file)
    sys.exit(0 if os.path.exists(output_file) else 1)
