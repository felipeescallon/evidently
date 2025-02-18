#!/usr/bin/env python
# coding: utf-8

import json
import pandas as pd

import numpy as np

from sklearn import metrics, preprocessing
from pandas.api.types import is_numeric_dtype

import plotly.graph_objs as go
import plotly.figure_factory as ff

from evidently.model.widget import BaseWidgetInfo, AlertStats, AdditionalGraphInfo
from evidently.widgets.widget import Widget

red = "#ed0400"
grey = "#4d4d4d"


class ProbClassProdPredDistrWidget(Widget):
    def __init__(self, title: str):
        super().__init__()
        self.title = title

    def get_info(self) -> BaseWidgetInfo:
        #if self.wi:
        return self.wi
        #raise ValueError("No prediction or target data provided")

    def calculate(self, reference_data: pd.DataFrame, production_data: pd.DataFrame, column_mapping): 
        if column_mapping:
            date_column = column_mapping.get('datetime')
            id_column = column_mapping.get('id')
            target_column = column_mapping.get('target')
            prediction_column = column_mapping.get('prediction')
            num_feature_names = column_mapping.get('numerical_features')
            #target_names = column_mapping.get('target_names')
            if num_feature_names is None:
                num_feature_names = []
            else:
                num_feature_names = [name for name in num_feature_names if is_numeric_dtype(reference_data[name])] 

            cat_feature_names = column_mapping.get('categorical_features')
            if cat_feature_names is None:
                cat_feature_names = []
            else:
                cat_feature_names = [name for name in cat_feature_names if is_numeric_dtype(reference_data[name])] 
        
        else:
            date_column = 'datetime' if 'datetime' in reference_data.columns else None
            id_column = None
            target_column = 'target' if 'target' in reference_data.columns else None
            prediction_column = 'prediction' if 'prediction' in reference_data.columns else None

            utility_columns = [date_column, id_column, target_column, prediction_column]

            num_feature_names = list(set(reference_data.select_dtypes([np.number]).columns) - set(utility_columns))
            cat_feature_names = list(set(reference_data.select_dtypes([np.object]).columns) - set(utility_columns))

            #target_names = None

        if production_data is not None and target_column is not None and prediction_column is not None:
            production_data.replace([np.inf, -np.inf], np.nan, inplace=True)
            production_data.dropna(axis=0, how='any', inplace=True)

            array_prediction = production_data[prediction_column].to_numpy()

            prediction_ids = np.argmax(array_prediction, axis=-1)
            prediction_labels = [prediction_column[x] for x in prediction_ids]
            
            #plot support bar
            graphs = []

            for label in prediction_column:
                pred_distr = ff.create_distplot(
                    [
                        production_data[production_data[target_column] == label][label], 
                        production_data[production_data[target_column] != label][label]
                    ], 
                    [str(label), "other"],  
                    colors=[red, grey],
                    bin_size = 0.05,
                    show_curve = False,
                    show_rug=True)

                pred_distr.update_layout(
                    xaxis_title = "Probability",
                    yaxis_title = "Share",
                    legend = dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                    )
                )

                pred_distr_json = json.loads(pred_distr.to_json())

                graphs.append({
                    "id": "tab_" + str(label),
                    "title": str(label),
                    "graph":{
                        "data":pred_distr_json["data"],
                        "layout":pred_distr_json["layout"],
                        }
                    })

            self.wi = BaseWidgetInfo(
                title=self.title,
                type="tabbed_graph",
                details="",
                alertStats=AlertStats(),
                alerts=[],
                alertsPosition="row",
                insights=[],
                size=1,
                params={
                    "graphs": graphs
                },
                additionalGraphs=[],
            )
        else:
            self.wi = None

