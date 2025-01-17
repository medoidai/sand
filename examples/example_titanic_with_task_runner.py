import os, datetime

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression

from skrobot.core import TaskRunner
from skrobot.tasks import TrainTask
from skrobot.tasks import PredictionTask
from skrobot.tasks import FeatureSelectionCrossValidationTask
from skrobot.tasks import EvaluationCrossValidationTask
from skrobot.tasks import HyperParametersSearchCrossValidationTask
from skrobot.feature_selection import ColumnSelector

######### Initialization Code

train_data_set = os.path.join('data', 'titanic-train.csv')

test_data_set = os.path.join('data', 'titanic-test.csv')

new_data_set = os.path.join('data', 'titanic-new.csv')

random_seed = 42

id_column = 'PassengerId'

label_column = 'Survived'

numerical_features = ['Age', 'Fare', 'SibSp', 'Parch']

categorical_features = ['Embarked', 'Sex', 'Pclass']

numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer()),
    ('scaler', StandardScaler())])

categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('encoder', OneHotEncoder(handle_unknown='ignore'))])

preprocessor = ColumnTransformer(transformers=[
    ('numerical_transformer', numeric_transformer, numerical_features),
    ('categorical_transformer', categorical_transformer, categorical_features)])

classifier = LogisticRegression(solver='liblinear', random_state=random_seed)

search_params = {
    "classifier__C" : [ 1.e-01, 1.e+00, 1.e+01 ],
    "classifier__penalty" : [ "l1", "l2" ],
    "preprocessor__numerical_transformer__imputer__strategy" : [ "mean", "median" ]
}

######### skrobot Code

# Create a Task Runner
task_runner = TaskRunner(f'task-runner-output-{datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")}')

# Run Feature Selection Task
features_columns = task_runner.run(FeatureSelectionCrossValidationTask (estimator=classifier,
                                                                        train_data_set=train_data_set,
                                                                        preprocessor=preprocessor,
                                                                        min_features_to_select=4,
                                                                        id_column=id_column,
                                                                        label_column=label_column,
                                                                        random_seed=random_seed).stratified_folds(total_folds=5, shuffle=True))

pipe = Pipeline(steps=[('preprocessor', preprocessor),
                       ('selector', ColumnSelector(cols=features_columns)),
                       ('classifier', classifier)])

# Run Hyperparameters Search Task
hyperparameters_search_results = task_runner.run(HyperParametersSearchCrossValidationTask (estimator=pipe,
                                                                                           search_params=search_params,
                                                                                           train_data_set=train_data_set,
                                                                                           id_column=id_column,
                                                                                           label_column=label_column,
                                                                                           random_seed=random_seed).random_search(n_iters=100).stratified_folds(total_folds=5, shuffle=True))

# Run Evaluation Task
evaluation_results = task_runner.run(EvaluationCrossValidationTask(estimator=pipe,
                                                                   estimator_params=hyperparameters_search_results['best_params'],
                                                                   train_data_set=train_data_set,
                                                                   test_data_set=test_data_set,
                                                                   id_column=id_column,
                                                                   label_column=label_column,
                                                                   random_seed=random_seed,
                                                                   export_classification_reports=True,
                                                                   export_confusion_matrixes=True,
                                                                   export_pr_curves=True,
                                                                   export_roc_curves=True,
                                                                   export_false_positives_reports=True,
                                                                   export_false_negatives_reports=True,
                                                                   export_also_for_train_folds=True).stratified_folds(total_folds=5, shuffle=True))

# Run Train Task
train_results = task_runner.run(TrainTask(estimator=pipe,
                                          estimator_params=hyperparameters_search_results['best_params'],
                                          train_data_set=train_data_set,
                                          id_column=id_column,
                                          label_column=label_column,
                                          random_seed=random_seed))

# Run Prediction Task
predictions = task_runner.run(PredictionTask(estimator=train_results['estimator'],
                                             data_set=new_data_set,
                                             id_column=id_column,
                                             prediction_column=label_column,
                                             threshold=evaluation_results['threshold']))

# Print in-memory results
print(features_columns)

print(hyperparameters_search_results['best_params'])
print(hyperparameters_search_results['best_index'])
print(hyperparameters_search_results['best_estimator'])
print(hyperparameters_search_results['best_score'])
print(hyperparameters_search_results['search_results'])

print(evaluation_results['threshold'])
print(evaluation_results['cv_threshold_metrics'])
print(evaluation_results['cv_splits_threshold_metrics'])
print(evaluation_results['cv_splits_threshold_metrics_summary'])
print(evaluation_results['test_threshold_metrics'])

print(train_results['estimator'])

print(predictions)