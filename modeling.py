import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.stats import pearsonr
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests

COVARIATES = [
    "age", "sex", "bmi", "smoking_binary",
    "oralhealth_soft_tissue_inflammation_level", "oralhealth_periodontal_damage_level",
]
N_SPLITS = 5
N_PERMUTATIONS = 500
LGBM_PARAMS = dict(
    objective="regression", max_depth=4, n_estimators=2000, learning_rate=0.001,
    subsample=0.5, subsample_freq=1, colsample_bytree=0.3, reg_alpha=1, reg_lambda=1,
    min_data_in_leaf=20, random_state=1, n_jobs=-1, verbosity=-1,
)


def build_lgbm():
    return lgb.LGBMRegressor(**LGBM_PARAMS)


def preprocess_fold(x_train, x_test):
    x_train = x_train.astype(float)
    x_test = x_test.astype(float)
    medians = x_train.median()
    x_train = x_train.fillna(medians)
    x_test = x_test.fillna(medians)
    continuous = [c for c in x_train.columns if not set(x_train[c].dropna().unique()) <= {0, 1}]
    if continuous:
        scaler = StandardScaler().fit(x_train[continuous].to_numpy())
        x_train.loc[:, continuous] = scaler.transform(x_train[continuous].to_numpy())
        x_test.loc[:, continuous] = scaler.transform(x_test[continuous].to_numpy())
    return x_train, x_test


def oof_predict(x, y):
    y = np.asarray(y, dtype=float)
    pred = np.full(len(y), np.nan)
    for train, test in KFold(n_splits=N_SPLITS, shuffle=False).split(x):
        x_train, x_test = preprocess_fold(x.iloc[train], x.iloc[test])
        y_scaler = StandardScaler().fit(y[train].reshape(-1, 1))
        model = build_lgbm().fit(x_train, y_scaler.transform(y[train].reshape(-1, 1)).ravel())
        pred[test] = y_scaler.inverse_transform(model.predict(x_test).reshape(-1, 1)).ravel()
    return pred


def prediction_metrics(y, pred):
    r, p = pearsonr(y, pred)
    return {"pearson_r": float(r), "pearson_p": float(p), "r2": float(r2_score(y, pred))}


def oof_pearson(x, y):
    return prediction_metrics(np.asarray(y, dtype=float), oof_predict(x, y))["pearson_r"]


def permuted(y, seed):
    return pd.Series(np.asarray(y, dtype=float)).sample(frac=1, random_state=seed).to_numpy()


def permutation_p(null, observed):
    null = np.asarray(null, dtype=float)
    null = null[np.isfinite(null)]
    return float((np.sum(null >= observed) + 1) / (len(null) + 1))


def bh_fdr(p_values):
    p = np.asarray(p_values, dtype=float)
    q = np.full(len(p), np.nan)
    valid = np.isfinite(p)
    if valid.any():
        q[valid] = multipletests(p[valid], method="fdr_bh")[1]
    return q
