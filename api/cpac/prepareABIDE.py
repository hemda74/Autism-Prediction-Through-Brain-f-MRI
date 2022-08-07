"""
  prepare_data.py --whole cc200
 
"""
import os
import random
import pandas as pd
import numpy as np
import numpy.ma as ma
from docopt import docopt
from functools import partial
from sklearn import preprocessing
from sklearn.model_selection import StratifiedKFold, train_test_split
from utils import (load_phenotypes, format_config, run_progress, hdf5_handler)


def compute_connectivity(functional):
    with np.errstate(invalid="ignore"):
        corr = np.nan_to_num(np.corrcoef(functional))
        mask = np.invert(np.tri(corr.shape[0], k=-1, dtype=bool))
        m = ma.masked_where(mask == 1, mask)
        return ma.masked_where(m, corr).compressed()


def load_patient(subj, tmpl):
    df = pd.read_csv(format_config(tmpl, {
        "subject": subj,
    }), sep="\t", header=0)
    df = df.apply(lambda x: pd.to_numeric(x, errors='coerce'))

    ROIs = ["#" + str(y) for y in sorted([int(x[1:]) for x in df.keys().tolist()])]

    functional = np.nan_to_num(df[ROIs].to_numpy().T).tolist()
    functional = preprocessing.scale(functional, axis=1)
    functional = compute_connectivity(functional)
    functional = functional.astype(np.float32)

    return subj, functional.tolist()


def load_patients(subjs, tmpl, jobs=1):
    partial_load_patient = partial(load_patient, tmpl=tmpl)
    msg = "Processing {current} of {total}"
    return dict(run_progress(partial_load_patient, subjs, message=msg, jobs=jobs))


def prepare_folds(hdf5, folds, pheno, derivatives, experiment):
    exps = hdf5.require_group("experiments")
    ids = pheno["FILE_ID"]

    for derivative in derivatives:
        exp = exps.require_group(format_config(
            experiment,
            {
                "derivative": derivative,
            }
        ))

        exp.attrs["derivative"] = derivative

        skf = StratifiedKFold(n_splits=folds, shuffle=True)
        for i, (train_index, test_index) in enumerate(skf.split(ids, pheno["STRAT"])):
            train_index, valid_index = train_test_split(train_index, test_size=0.33)
            fold = exp.require_group(str(i))

            fold['train'] = [ind.encode('utf8') for ind in ids[train_index]] 

            fold['valid'] = [indv.encode('utf8') for indv in ids[valid_index]]
 
            fold["test"] = [indt.encode('utf8') for indt in ids[test_index]]




def load_patients_to_file(hdf5, pheno, derivatives):

    download_root = "./data/functionals"
    derivatives_path = {
        "cc200": "cpac/filt_global/rois_cc200/{subject}_rois_cc200.1D",
    }

    storage = hdf5.require_group("patients")
    file_ids = pheno["FILE_ID"].tolist()

    for derivative in derivatives:

        file_template = os.path.join(download_root, derivatives_path[derivative])
        func_data = load_patients(file_ids, tmpl=file_template)

        for pid in func_data:
            print('func_data_filling')
            record = pheno[pheno["FILE_ID"] == pid].iloc[0]
            patient_storage = storage.require_group(pid)
            patient_storage.attrs["id"] = record["FILE_ID"]
            patient_storage.attrs["y"] = record["DX_GROUP"]
            patient_storage.attrs["site"] = record["SITE_ID"]
            patient_storage.attrs["sex"] = record["SEX"]
            patient_storage.create_dataset(derivative, data=func_data[pid])

if __name__ == "__main__":

    random.seed(19)
    np.random.seed(19)

    arguments = docopt(__doc__)

    folds = int(arguments["--folds"])
    pheno_path = "./data/phenotypes/Phenotypic_V1_0b_preprocessed1.csv"
    pheno = load_phenotypes(pheno_path)

    hdf5 = hdf5_handler(bytes("./data/abide.hdf5",encoding="utf8"), "a+")

    valid_derivatives = ["cc200"]
    derivatives = [derivative for derivative in arguments["<derivative>"] if derivative in valid_derivatives]

    if "patients" not in hdf5:
        load_patients_to_file(hdf5, pheno, derivatives)

    if arguments["--whole"]:
        
        print ("ABIDE preparing...")
        prepare_folds(hdf5, folds, pheno, derivatives, experiment="{derivative}_whole")

    