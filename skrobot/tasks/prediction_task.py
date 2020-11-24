import os, copy

import pandas as pd

from . import BaseTask

class PredictionTask(BaseTask):
  """
  The :class:`.PredictionTask` class can be used to predict new data using a scikit-learn estimator. It extends the :class:`.BaseTask` class.
  """
  def __init__ (self, estimator, data_set_file_path, field_delimiter=',', feature_columns='all', id_column='id', prediction_column='prediction', threshold=0.5):
    """
    This is the constructor method and can be used to create a new object instance of :class:`.PredictionTask` class.

    :param estimator: It can be either a scikit-learn estimator (e.g., LogisticRegression) or a scikit-learn pipeline ending with an estimator. The estimator needs to be able to predict probabilities through a ``predict_proba`` method.
    :type estimator: scikit-learn {estimator, pipeline} object

    :param data_set_file_path: The file path of the input data set. It can be either a URL or a disk file path.
    :type data_set_file_path: str

    :param field_delimiter: The separation delimiter (comma for CSV, tab for TSV, etc.) used in the input data set file. It defaults to ','.
    :type field_delimiter: str, optional

    :param feature_columns: Either 'all' to use from the input data set file all the columns or a list of column names to select specific columns. It defaults to 'all'.
    :type feature_columns: {str, list}, optional

    :param id_column: The name of the column in the input data set file containing the sample IDs. It defaults to 'id'.
    :type id_column: str, optional

    :param prediction_column: The name of the column for the predicted binary class labels. It defaults to 'prediction'.
    :type prediction_column: str, optional

    :param threshold: The threshold to use for converting the predicted probability into a binary class label. It defaults to 0.5.
    :type threshold: float, optional
    """

    arguments = copy.deepcopy(locals())

    super(PredictionTask, self).__init__(PredictionTask.__name__, arguments)

  def run(self, output_directory):
    """
    A method for running the task.

    The predictions are returned as a result and also stored in a *predictions.csv* CSV file under the output directory path.

    :param output_directory: The output directory path under which task-related generated files are stored.
    :type output_directory: str

    :return: The predictions for the input data set. Specifically, the result contains the sample IDs, the predicted binary class labels, and the predicted probabilities for the positive class.
    :rtype: pandas DataFrame
    """

    data_set_data_frame = pd.read_csv(self.data_set_file_path, delimiter=self.field_delimiter)

    ids = data_set_data_frame[self.id_column]

    X = data_set_data_frame.drop(columns=[self.id_column])

    if self.feature_columns != 'all':
      X = X[self.feature_columns]

    predictions = pd.DataFrame({ self.id_column : ids, self.prediction_column : self._calculate_y_hat_for_threshold(self.estimator, X, self.threshold), "probability" : self._calculate_probability(self.estimator, X)})

    predictions.to_csv(os.path.join(output_directory, f'predictions.csv'), index=False)

    return predictions

  def _calculate_y_hat_for_threshold (self, estimator, X, threshold):
    y_proba = estimator.predict_proba(X)

    y_hat = y_proba[:, 1] >= threshold

    return y_hat.astype(int)

  def _calculate_probability(self, estimator, X):
    y_proba = estimator.predict_proba(X)

    return y_proba[:, 1]