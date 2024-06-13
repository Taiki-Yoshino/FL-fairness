import numpy as np
from utils.fairness import fairness
from models.model import LogisticRegression 

def get_xys(data):
    x, y, s = [], [], []
    for group in ['A0', 'A1', 'B0', 'B1']:
        x.extend(data[group]['x'])
        y.extend(data[group]['y'])
        s.extend(data[group]['s'])  
    return np.array(x), np.array(y), np.array(s)


def standalone(x, y , s, lr, epochs): 
    n_features = x.shape[1]
    model = LogisticRegression(epochs=epochs, n_features=n_features, lr=lr)
    model.train(x, y)
    y_pred = model.predict(x)
    pred_acc = (y_pred == y)
    acc = np.mean(pred_acc)
    s_eo, s_dp = fairness(y, y_pred, pred_acc, s)
    decision_boundary = - model.b/ model.w
    return acc, s_eo, s_dp, decision_boundary[0]

def bruteforce(x, y, s, search_range, step, warm_start = None):
    best_decision_boundary = 0
    best_acc = 0
    lower_range = warm_start - search_range
    upper_range = warm_start + search_range
    
    iteration = int((upper_range - lower_range) /step)
    
    for i in range(iteration):
        decision_boundary = lower_range + step * i
        y_pred = [1 if value > decision_boundary else 0 for value in x]
        acc = np.mean((y_pred == y))
        if(best_acc < acc):
            best_decision_boundary = decision_boundary
            best_acc = acc
    #compute fairness 
    y_pred = np.array([1 if value > best_decision_boundary else 0 for value in x])
    pred_acc = (y_pred == y)
    s_eo, s_dp = fairness(y, y_pred, pred_acc, s)
    return best_acc, s_eo, s_dp, best_decision_boundary

def centralized(global_data, lr, epochs):
    x, y, s = get_xys(global_data)
    x = x.reshape(-1,1)
    acc, s_eo, s_dp, decision_boundary = standalone(x, y, s, lr, epochs)
    return acc, s_eo, s_dp, decision_boundary

def fedavg(combined_data, global_data, lr, epochs):
    fedavg_weight = None
    fedavg_bias = None
    fedavg_model = None
    #training
    for i in range(epochs):
        local_weights = []
        local_biases = []
        for client in global_data: 
            x, y, s = get_xys(client)
            x = x.reshape(-1,1)
            n_features = x.shape[1]
            model = LogisticRegression(epochs=1, n_features=n_features, lr=lr, weight=fedavg_weight, intercept=fedavg_bias)
            model.train(x,y)
            local_weights.append(model.w.tolist())
            local_biases.append(model.b.tolist())
            fedavg_model = model
        fedavg_weight = np.array(local_weights).mean(axis=0)
        fedavg_bias = np.array(local_biases).mean(axis=0)
    #eval 
    x, y, s = get_xys(combined_data)
    x = x.reshape(-1,1)
    y_pred = fedavg_model.predict(x)
    pred_acc = (y_pred == y)
    acc = np.mean(pred_acc)
    s_eo, s_dp = fairness(y, y_pred, pred_acc, s)
    decision_boundary = - model.b/ model.w
    return acc, s_eo, s_dp, decision_boundary[0]