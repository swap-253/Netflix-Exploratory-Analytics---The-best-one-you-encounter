import pandas as pd
from pandas.core import indexing
import numpy as np
import warnings
import pickle
import random
import json
import re

# import nltk
import random
import os
import math
import string
import stop_words

# import nltk

# from nltk.tokenize import word_tokenize
# from nltk.corpus import stopwords
from collections import Counter, ChainMap
from datetime import timedelta
from dateutil.parser import parse

warnings.filterwarnings("ignore")

# nltk.data.path.append("/var/task/nltk_data")
# nltk.download()
# from nltk.stem import WordNetLemmatizer
# from nltk.stem.wordnet import WordNetLemmatizer

pd.options.display.max_rows = None
pd.options.display.max_columns = None


## trying to capture keyword like " sal " and " sal". In this case, narrations with salau will fail because no exact match with " sal ".
## mar[0-9][0-9][0-9]?[0-9]? tries to find match like mar2019, mar20, or mar201  that's why I used the ?
## this salary_keywords variable is used across different functions in the rules that make up salary module

salary_keywords = r"(salary|^salary | salary |slr| sal | sal$|sal$| salar |salar$|jan ?sal| sala$|\
                     |feb ?sal|mar ?sal|apr ?sal|may ?sal|jun ?sal|jul ?sal|aug ?sal|\
                     |sept ?sal|oct ?sal|nov ?sal|dec ?sal|jan[0-9][0-9][0-9]?[0-9]?|feb[0-9][0-9][0-9]?[0-9]?|\
                     |mar[0-9][0-9][0-9]?[0-9]?|apr[0-9][0-9][0-9]?[0-9]?|may[0-9][0-9][0-9]?[0-9]?|\
                     |jun[0-9][0-9][0-9]?[0-9]?|jul[0-9][0-9][0-9]?[0-9]?|aug[0-9][0-9][0-9]?[0-9]?|\
                     |sep[0-9][0-9][0-9]?[0-9]?|oct[0-9][0-9][0-9]?[0-9]?|nov[0-9][0-9][0-9]?[0-9]?|\
                     |dec[0-9][0-9][0-9]?[0-9]?|january[0-9][0-9][0-9]?[0-9]?|february[0-9][0-9][0-9]?[0-9]?|\
                     |march[0-9][0-9][0-9]?[0-9]?|april[0-9][0-9][0-9]?[0-9]?|may[0-9][0-9][0-9]?[0-9]?|\
                     |june[0-9][0-9][0-9]?[0-9]?|july[0-9][0-9][0-9]?[0-9]?|august[0-9][0-9][0-9]?[0-9]?|\
                     |september[0-9][0-9][0-9]?[0-9]?|october[0-9][0-9][0-9]?[0-9]?|november[0-9][0-9][0-9]?[0-9]?|\
                     |december[0-9][0-9][0-9]?[0-9]?)"


## filter by the loan disbursements keywords and others (removing observations that have those keywords)
keywords = [
    "loan",
    "palmcredit",
    "kwikmoney",
    "lendigo",
    "branch",
    "swiss credit",
    "reversal",
    "cash dep",
    "888sport",
    "deposit",
    "deduct",
    "fairmoney",
    "13th month",
    "credit direct",
    "piggyvest",
    "disbursement credit",
    "sporty",
    "bonus",
    "renmoney",
    "loan repayment",
    "loan repymt",
    "loan rpmt",
    "allowance",
    "pos",
    "merrybet",
    "bet",
    "bill",
]

## One - This function filters transaction_narration and returns all rows where the 10 most occuring keywords occur
def filter_by_transaction_narration(data, salary_variables):
    try:
        list_stopwords = set(stop_words.get_stop_words("en"))  # About 174 stopwords
        data["description"] = data["description"].str.lower()
        data["description"] = data["description"].str.rstrip()
        data["description"] = data["description"].str.lstrip()
        data["description"] = data["description"].apply(
            lambda x: " ".join(re.split(";|,|:|/|@|-|=|_|#", str(x)))
        )
        data["description"] = (
            data["description"]
            .str.replace("\(", " ")
            .str.replace("\)", " ")
            .str.replace("\\", " ")
        )
        data["description"] = (
            data["description"]
            .str.replace("[", " ")
            .str.replace("]", " ")
            .str.replace("@", " ")
            .str.replace("*", " ")
            .str.replace("?", " ") 

        )

        data["description"] = data["description"].apply(
            lambda x: " ".join(
                [word for word in x.split() if word not in (list_stopwords)]
            )
        )
        data = data[data.type.isin(["credit", "C", "c", "Credit"])]

        data["description"] = data["description"].str.replace("\(", ">>")
        data["description"] = data["description"].str.replace("\)", "<<")

        filter_one = data[(data["amount"] > salary_variables["amountGreaterThan"])]
        filter_one["description"] = filter_one["description"].apply(
            lambda x: x.replace("*", " ")
        )

        most_occuring = [
            values[0]
            for values in Counter(
                " ".join(filter_one["description"]).split()
            ).most_common(10)
        ]
        search_list = "|".join(most_occuring)
        search_list = r"{}".format(search_list)
        df = filter_one[filter_one["description"].str.contains(search_list)]

        ## filter by keyword
        df = df[~df.description.str.contains("|".join(keywords))]

    except TypeError:
        print(
            "you can only filter natrration for a pandas dataframe not (list,dict, tuple or set)"
        )

    else:
        return df


## Two - This function filters by amount and returns the first most occuring transactions (plus transactions that are +-13% away from first_modal amounts)
def filter_by_first_modal(data, salary_variables):
    if data.empty:
        first_modal = pd.DataFrame(columns=data.columns)
        first_modal["modal_class"] = "One"
        first_modal["date_flag"] = ""

    ## I implemented the max logic to capture cases where the transaction amount is unique (i.e. when no two transaction amounts are the same)
    elif max(data["amount"].value_counts()) == 1:
        recommended_max_val_1 = np.percentile(data["amount"], 80) * (
            1 + salary_variables["salaryAmountThreshold"]
        )
        recommended_min_val_1 = np.percentile(data["amount"], 80) * (
            1 - salary_variables["salaryAmountThreshold"]
        )
        first_modal = data[
            data["amount"].apply(
                lambda x: recommended_min_val_1 <= x <= recommended_max_val_1
            )
        ]
        first_modal["modal_class"] = "One"

        if first_modal.empty:
            first_modal = pd.DataFrame(columns=data.columns)
            first_modal["date_flag"] = ""

        else:
            first_modal = first_modal
            first_modal["date"] = pd.to_datetime(first_modal["date"])
            first_modal = first_modal.sort_values("date", ascending=True)

            first_modal["difference_in_days"] = (
                first_modal.groupby("modal_class")["date"]
                .diff()
                .fillna(pd.Timedelta("0 days"))
                .dt.days
            )

        # conditions for logic below:
        # 1. checks if payment day for index transaction is +-3 days away from the modal day for other non-index transactions or
        # 2. checks if the salary keywords are in the index transaction narration
        # 3. checks if the amount for index transaction is +- 10% away from the mean amount of other non-mean trans
        # 4. if any of the three conditions return true then difference_in_days for index transaction is set to 30 else 0
        # 5. I used the first len condition to handle scenarios when only a single transaction is returned (i.e. no data.iloc[1:] but only data.iloc[0]). In such scenario, the difference_in_days is set to 0

        if len(first_modal) > 1:
            if (
                (first_modal.iloc[1:]["date"].dt.day.mode()[0] - 3)
                <= first_modal.iloc[0]["date"].day
                <= (first_modal.iloc[1:]["date"].dt.day.mode()[0] + 3)
                or any(x in first_modal.iloc[0]["description"] for x in salary_keywords)
                or (
                    (first_modal.iloc[1:]["amount"].mean() * 0.9)
                    <= first_modal.iloc[0]["amount"]
                    <= (first_modal.iloc[1:]["amount"].mean() * 1.1)
                )
            ):

                first_modal.head(1)["difference_in_days"] = 30
            else:
                first_modal.head(1)["difference_in_days"] = 0

            first_modal["date_flag"] = first_modal["difference_in_days"].apply(
                lambda x: 1
                if (
                    salary_variables["maxDifferenceInPaymentDays"]
                    >= x
                    >= salary_variables["minDifferenceInPaymentDays"]
                )
                else 0
            )

            # Might not use this for the first modal class
            if (
                first_modal["date_flag"].mean()
                >= salary_variables["thresholdForDifferenceInDaysOccurence"]
            ):
                first_modal = first_modal
            else:
                first_modal = pd.DataFrame(columns=data.columns)

        else:
            first_modal = pd.DataFrame(columns=data.columns)

    else:
        recommended_max_val_1 = data.amount.value_counts().index[:3].values[0] * (
            1 + salary_variables["salaryAmountThreshold"]
        )
        recommended_min_val_1 = data.amount.value_counts().index[:3].values[0] * (
            1 - salary_variables["salaryAmountThreshold"]
        )
        first_modal = data[
            data["amount"].apply(
                lambda x: recommended_min_val_1 <= x <= recommended_max_val_1
            )
        ]
        first_modal["modal_class"] = "One"

        first_modal["date"] = pd.to_datetime(first_modal["date"])
        first_modal = first_modal.sort_values("date", ascending=True)
        first_modal["difference_in_days"] = (
            first_modal.groupby("modal_class")["date"]
            .diff()
            .fillna(pd.Timedelta("0 days"))
            .dt.days
        )

        # conditions for logic below:
        # 1. checks if payment day for index transaction is +-3 days away from the modal day for other non-index transactions or
        # 2. checks if the salary keywords are in the index transaction narration
        # 3. checks if the amount for index transaction is +- 10% away from the mean amount of other non-mean trans
        # 4. if any of the three conditions return true then difference_in_days for index transaction is set to 30 else 0
        # 5. I used the first len condition to handle scenarios when only a single transaction is returned (i.e. no data.iloc[1:] but only data.iloc[0]). In such scenario, the difference_in_days is set to 0

        if len(first_modal) > 1:
            if (
                (first_modal.iloc[1:]["date"].dt.day.mode()[0] - 3)
                <= first_modal.iloc[0]["date"].day
                <= (first_modal.iloc[1:]["date"].dt.day.mode()[0] + 3)
                or (
                    any(
                        x in first_modal.iloc[0]["description"] for x in salary_keywords
                    )
                )
                or (
                    (first_modal.iloc[1:]["amount"].mean() * 0.9)
                    <= first_modal.iloc[0]["amount"]
                    <= (first_modal.iloc[1:]["amount"].mean() * 1.1)
                )
            ):

                first_modal.head(1)["difference_in_days"] = 30
            else:
                first_modal.head(1)["difference_in_days"] = 0

            first_modal["date_flag"] = first_modal["difference_in_days"].apply(
                lambda x: 1
                if (
                    salary_variables["maxDifferenceInPaymentDays"]
                    >= x
                    >= salary_variables["minDifferenceInPaymentDays"]
                )
                else 0
            )

            # Might not use this for the first modal class
            if (
                first_modal["date_flag"].mean()
                >= salary_variables["thresholdForDifferenceInDaysOccurence"]
            ):
                first_modal = first_modal
            else:
                first_modal = pd.DataFrame(columns=data.columns)
        else:
            first_modal = pd.DataFrame(columns=data.columns)

    return first_modal


## Three - This function filters by amount and returns the second most occuring transactions (plus transactions that are +-13% away from second_modal amounts)
def filter_by_second_modal(data, salary_variables):
    # defaulting any dataframe with len of 1 to empty because I already handled that in the first_modal logic
    if len(data["amount"].value_counts()) == 1 or data.empty:
        second_modal = pd.DataFrame(columns=data.columns)
        second_modal["modal_class"] = "Two"
        second_modal["date_flag"] = ""
    else:
        recommended_max_val_2 = data["amount"].value_counts().index[:3].values[1] * (
            1 + salary_variables["salaryAmountThreshold"]
        )
        recommended_min_val_2 = data["amount"].value_counts().index[:3].values[1] * (
            1 - salary_variables["salaryAmountThreshold"]
        )

        second_modal = data[
            data["amount"].apply(
                lambda x: recommended_min_val_2 <= x <= recommended_max_val_2
            )
        ]
        second_modal["modal_class"] = "Two"

        second_modal["date"] = pd.to_datetime(second_modal["date"])
        second_modal = second_modal.sort_values("date", ascending=True)
        second_modal["difference_in_days"] = (
            second_modal.groupby("modal_class")["date"]
            .diff()
            .fillna(pd.Timedelta("0 days"))
            .dt.days
        )

        # conditions for logic below:
        # 1. checks if payment day for index transaction is +-3 days away from the modal day for other non-index transactions or
        # 2. checks if the salary keywords are in the index transaction narration
        # 3. checks if the amount for index transaction is +- 10% away from the mean amount of other non-mean trans
        # 4. if any of the three conditions return true then difference_in_days for index transaction is set to 30 else 0
        # 5. I used the first len condition to handle scenarios when only a single transaction is returned (i.e. no data.iloc[1:] but only data.iloc[0]). In such scenario, the difference_in_days is set to 0

        if len(second_modal) > 1:
            if (
                (second_modal.iloc[1:]["date"].dt.day.mode()[0] - 3)
                <= second_modal.iloc[0]["date"].day
                <= (second_modal.iloc[1:]["date"].dt.day.mode()[0] + 3)
                or (
                    any(
                        x in second_modal.iloc[0]["description"]
                        for x in salary_keywords
                    )
                )
                or (
                    (second_modal.iloc[1:]["amount"].mean() * 0.9)
                    <= second_modal.iloc[0]["amount"]
                    <= (second_modal.iloc[1:]["amount"].mean() * 1.1)
                )
            ):

                second_modal.head(1)["difference_in_days"] = 30
            else:
                second_modal.head(1)["difference_in_days"] = 0
        else:
            second_modal.head(1)["difference_in_days"] = 0

        second_modal["date_flag"] = second_modal["difference_in_days"].apply(
            lambda x: 1
            if (
                salary_variables["maxDifferenceInPaymentDays"]
                >= x
                >= salary_variables["minDifferenceInPaymentDays"]
            )
            else 0
        )

        if (
            second_modal.date_flag.mean()
            >= salary_variables["thresholdForDifferenceInDaysOccurence"]
        ):
            second_modal = second_modal
        else:
            second_modal = pd.DataFrame(columns=data.columns)
            second_modal["modal_class"] = ""

    return second_modal


## Four - This function filters by amount and returns the third most occuring transactions (plus transactions that are +-13% away from third_modal amounts)
def filter_by_third_modal(data, salary_variables):

    if len(data["amount"].value_counts()) <= 2 or data.empty:
        third_modal = pd.DataFrame(columns=data.columns)
        third_modal["modal_class"] = "Three"
        third_modal["date_flag"] = ""
    else:
        recommended_max_val_2 = data["amount"].value_counts().index[:3].values[2] * (
            1 + salary_variables["salaryAmountThreshold"]
        )
        recommended_min_val_2 = data["amount"].value_counts().index[:3].values[2] * (
            1 - salary_variables["salaryAmountThreshold"]
        )

        third_modal = data[
            data["amount"].apply(
                lambda x: recommended_min_val_2 <= x <= recommended_max_val_2
            )
        ]
        third_modal["modal_class"] = "Three"

        third_modal["date"] = pd.to_datetime(third_modal["date"])
        third_modal = third_modal.sort_values("date", ascending=True)
        third_modal["difference_in_days"] = (
            third_modal.groupby("modal_class")["date"]
            .diff()
            .fillna(pd.Timedelta("0 days"))
            .dt.days
        )

        # conditions for logic below:
        # 1. checks if payment day for index transaction is +-3 days away from the modal day for other non-index transactions or
        # 2. checks if the salary keywords are in the index transaction narration
        # 3. checks if the amount for index transaction is +- 10% away from the mean amount of other non-mean trans
        # 4. if any of the three conditions return true then difference_in_days for index transaction is set to 30 else 0
        # 5. I used the first len condition to handle scenarios when only a single transaction is returned (i.e. no data.iloc[1:] but only data.iloc[0]). In such scenario, the difference_in_days is set to 0

        if len(third_modal) > 1:
            if (
                (third_modal.iloc[1:]["date"].dt.day.mode()[0] - 3)
                <= third_modal.iloc[0]["date"].day
                <= (third_modal.iloc[1:]["date"].dt.day.mode()[0] + 3)
                or (
                    any(
                        x in third_modal.iloc[0]["description"] for x in salary_keywords
                    )
                )
                or (
                    (third_modal.iloc[1:]["amount"].mean() * 0.9)
                    <= third_modal.iloc[0]["amount"]
                    <= (third_modal.iloc[1:]["amount"].mean() * 1.1)
                )
            ):

                third_modal.head(1)["difference_in_days"] = 30
            else:
                third_modal.head(1)["difference_in_days"] = 0
        else:
            third_modal.head(1)["difference_in_days"] = 0

        third_modal["date_flag"] = third_modal["difference_in_days"].apply(
            lambda x: 1
            if (
                salary_variables["maxDifferenceInPaymentDays"]
                >= x
                >= salary_variables["minDifferenceInPaymentDays"]
            )
            else 0
        )

        if (
            third_modal.date_flag.mean()
            >= salary_variables["thresholdForDifferenceInDaysOccurence"]
        ):
            third_modal = third_modal
        else:
            third_modal = pd.DataFrame(columns=data.columns)
            third_modal["modal_class"] = ""

    return third_modal


## Five - This function filters by amount and returns the fourth most occuring transactions (plus transactions that are +-13% away from fourth_modal amounts)
def filter_by_fourth_modal(data, salary_variables):

    if len(data["amount"].value_counts()) <= 3 or data.empty:
        fourth_modal = pd.DataFrame(columns=data.columns)
        fourth_modal["modal_class"] = "Four"
        fourth_modal["date_flag"] = ""
    else:
        recommended_max_val_2 = data["amount"].value_counts().index[:4].values[3] * (
            1 + salary_variables["salaryAmountThreshold"]
        )
        recommended_min_val_2 = data["amount"].value_counts().index[:4].values[3] * (
            1 - salary_variables["salaryAmountThreshold"]
        )

        fourth_modal = data[
            data["amount"].apply(
                lambda x: recommended_min_val_2 <= x <= recommended_max_val_2
            )
        ]
        fourth_modal["modal_class"] = "Four"
        fourth_modal["date"] = pd.to_datetime(fourth_modal["date"])
        fourth_modal = fourth_modal.sort_values("date", ascending=True)
        fourth_modal["difference_in_days"] = (
            fourth_modal.groupby("modal_class")["date"]
            .diff()
            .fillna(pd.Timedelta("0 days"))
            .dt.days
        )

        # conditions for logic below:
        # 1. checks if payment day for index transaction is +-3 days away from the modal day for other non-index transactions or
        # 2. checks if the salary keywords are in the index transaction narration
        # 3. checks if the amount for index transaction is +- 10% away from the mean amount of other non-mean trans
        # 4. if any of the three conditions return true then difference_in_days for index transaction is set to 30 else 0
        # 5. I used the first len condition to handle scenarios when only a single transaction is returned (i.e. no data.iloc[1:] but only data.iloc[0]). In such scenario, the difference_in_days is set to 0

        if len(fourth_modal) > 1:
            if (
                (fourth_modal.iloc[1:]["date"].dt.day.mode()[0] - 3)
                <= fourth_modal.iloc[0]["date"].day
                <= (fourth_modal.iloc[1:]["date"].dt.day.mode()[0] + 3)
                or (
                    any(
                        x in fourth_modal.iloc[0]["description"]
                        for x in salary_keywords
                    )
                )
                or (
                    (fourth_modal.iloc[1:]["amount"].mean() * 0.9)
                    <= fourth_modal.iloc[0]["amount"]
                    <= (fourth_modal.iloc[1:]["amount"].mean() * 1.1)
                )
            ):

                fourth_modal.head(1)["difference_in_days"] = 30
            else:
                fourth_modal.head(1)["difference_in_days"] = 0
        else:
            fourth_modal.head(1)["difference_in_days"] = 0

        fourth_modal["date_flag"] = fourth_modal["difference_in_days"].apply(
            lambda x: 1
            if (
                salary_variables["maxDifferenceInPaymentDays"]
                >= x
                >= salary_variables["minDifferenceInPaymentDays"]
            )
            else 0
        )

        if (
            fourth_modal.date_flag.mean()
            >= salary_variables["thresholdForDifferenceInDaysOccurence"]
        ):
            fourth_modal = fourth_modal
        else:
            fourth_modal = pd.DataFrame(columns=data.columns)
            fourth_modal["modal_class"] = ""

    return fourth_modal


## Six - This function filters by amount and returns the fifth most occuring transactions (plus transactions that are +-13% away from fifth_modal amounts)
def filter_by_fifth_modal(data, salary_variables):

    if len(data["amount"].value_counts()) <= 4 or data.empty:
        fifth_modal = pd.DataFrame(columns=data.columns)
        fifth_modal["modal_class"] = "Five"
        fifth_modal["date_flag"] = ""
    else:
        recommended_max_val_2 = data["amount"].value_counts().index[:5].values[4] * (
            1 + salary_variables["salaryAmountThreshold"]
        )
        recommended_min_val_2 = data["amount"].value_counts().index[:5].values[4] * (
            1 - salary_variables["salaryAmountThreshold"]
        )

        fifth_modal = data[
            data["amount"].apply(
                lambda x: recommended_min_val_2 <= x <= recommended_max_val_2
            )
        ]
        fifth_modal["modal_class"] = "Five"

        fifth_modal["date"] = pd.to_datetime(fifth_modal["date"])
        fifth_modal["difference_in_days"] = (
            fifth_modal.groupby("modal_class")["date"]
            .diff()
            .fillna(pd.Timedelta("0 days"))
            .dt.days
        )

        # conditions for logic below:
        # 1. checks if payment day for index transaction is +-3 days away from the modal day for other non-index transactions or
        # 2. checks if the salary keywords are in the index transaction narration
        # 3. checks if the amount for index transaction is +- 10% away from the mean amount of other non-mean trans
        # 4. if any of the three conditions return true then difference_in_days for index transaction is set to 30 else 0
        # 5. I used the first len condition to handle scenarios when only a single transaction is returned (i.e. no data.iloc[1:] but only data.iloc[0]). In such scenario, the difference_in_days is set to 0

        if len(fifth_modal) > 1:
            if (
                (fifth_modal.iloc[1:]["date"].dt.day.mode().values[0] - 3)
                <= fifth_modal.iloc[0]["date"].day
                <= (fifth_modal.iloc[1:]["date"].dt.day.mode().values[0] + 3)
                or (
                    any(
                        x in fifth_modal.iloc[0]["description"] for x in salary_keywords
                    )
                )
                or (
                    (fifth_modal.iloc[1:]["amount"].mean() * 0.9)
                    <= fifth_modal.iloc[0]["amount"]
                    <= (fifth_modal.iloc[1:]["amount"].mean() * 1.1)
                )
            ):

                fifth_modal.head(1)["difference_in_days"] = 30
            else:
                fifth_modal.head(1)["difference_in_days"] = 0
        else:
            fifth_modal.head(1)["difference_in_days"] = 0

        fifth_modal["date_flag"] = fifth_modal["difference_in_days"].apply(
            lambda x: 1
            if (
                salary_variables["maxDifferenceInPaymentDays"]
                >= x
                >= salary_variables["minDifferenceInPaymentDays"]
            )
            else 0
        )

        if (
            fifth_modal.date_flag.mean()
            >= salary_variables["thresholdForDifferenceInDaysOccurence"]
        ):
            fifth_modal = fifth_modal
        else:
            fifth_modal = pd.DataFrame(columns=data.columns)
            fifth_modal["modal_class"] = ""

    return fifth_modal


## Seven- This function concatenates the first five modal results and then sort the dataframe by modal_class
def combine_five_modes(first, second, third, fourth, fifth):
    second_filtered = (
        pd.concat([first, second, third, fourth, fifth])
        .sort_values(by=["modal_class"])
        .reset_index()
        .drop("index", axis=1)
    )
    return second_filtered


## Eight - This function removes all duplicates using the transaction date and narration
def drop_duplicates(data):
    data = data.drop_duplicates(subset=["date", "description"], keep="last")
    return data


## Nine - This function filters by the transaction amount, returning all statements that are +/- 13% away from the 95th percentile value
## I had to increase the threshold here because it's most likely certain that values returned will be recurrent and salaries
## I would have used the modal value but not a best approach because not all modal amount turns out to be salary. You can have a salary appearing maybe twice while a non-salary appears six times e.t.c
def filter_by_transaction_amount(data, salary_variables):

    if data.empty:
        third_filtered = pd.DataFrame(columns=data.columns)
    else:
        recommended_max_final_1 = np.percentile(data["amount"], q=95) * (
            1 + salary_variables["salaryAmountThreshold"]
        )
        recommended_min_final_1 = np.percentile(data["amount"], q=95) * (
            1 - salary_variables["salaryAmountThreshold"]
        )

        third_filtered = data[
            data["amount"].apply(
                lambda x: recommended_min_final_1 <= x <= recommended_max_final_1
            )
        ]

    return third_filtered


## Ten - This function filters by actual salary keywords. The idea is to combine actual salary with the third_filtered and then drop duplicates
##  Sometimes, salaries will have keywords. Other times, It won't have keywords. This is me just implementing different ideas
def filter_by_salary_keywords(data, salary_variables):

    list_stopwords = set(stop_words.get_stop_words("en"))  # About 174 stopwords
    data["description"] = data["description"].str.lower()
    data["description"] = data["description"].str.rstrip()
    data["description"] = data["description"].str.lstrip()
    data["description"] = data["description"].apply(
        lambda x: " ".join(re.split(";|,|:|/|@|-|=|_|#", str(x)))
    )

    data["description"] = data["description"].apply(
        lambda x: " ".join([word for word in x.split() if word not in (list_stopwords)])
    )
    data = data[data.type.isin(["credit", "C", "c", "Credit"])]
    data = data[(data["amount"] > salary_variables["amountGreaterThan"])]

    ## filter by the loan disbursements keywords and others (removing observations that have those keywords)
    data = data[~data.description.str.contains("|".join(keywords))]

    actual_salary = data[data["description"].str.contains(salary_keywords)]

    if actual_salary.empty:
        actual_salary = pd.DataFrame(columns=data.columns)
        actual_salary["modal_class"] = "Six"
        actual_salary["date_flag"] = ""
    else:
        actual_salary = actual_salary
        actual_salary["modal_class"] = "Six"
        actual_salary["date"] = pd.to_datetime(actual_salary["date"])

    return actual_salary


## Eleven - This function combines third_filtered (output from first to fifth modal class, filtered by transacted amount) and actual_salary transactions
def combine_both_outputs(first, second):
    final_output = pd.concat([first, second])
    return final_output


## Twelve: This main function calls every other function above and returns an output
def calculate_salary(data, salary_variables):
    ## filter by transaction narration
    first_filtered = filter_by_transaction_narration(data, salary_variables)

    ## filter by transaction date
    final_first_modal = filter_by_first_modal(
        first_filtered, salary_variables
    )  ## first modal value
    final_second_modal = filter_by_second_modal(
        first_filtered, salary_variables
    )  ## second modal value
    final_third_modal = filter_by_third_modal(
        first_filtered, salary_variables
    )  ## third modal value
    final_fourth_modal = filter_by_fourth_modal(
        first_filtered, salary_variables
    )  ## fourth modal value
    final_fifth_modal = filter_by_fifth_modal(
        first_filtered, salary_variables
    )  ## fifth modal value
    second_filtered = combine_five_modes(  ## combine all five modal data
        final_first_modal,
        final_second_modal,
        final_third_modal,
        final_fourth_modal,
        final_fifth_modal,
    )
    second_filtered = drop_duplicates(second_filtered)  ## remove duplicates

    ## filter by transaction amount
    third_filtered = filter_by_transaction_amount(second_filtered, salary_variables)

    ## filter actual salary transactions using salary keywords
    actual_salary_filter = filter_by_salary_keywords(data, salary_variables)

    ## combine third_filtered, actual_salary and remove duplicates
    fourth_filtered = combine_both_outputs(third_filtered, actual_salary_filter)
    unduplicated_data = drop_duplicates(fourth_filtered)
    unduplicated_data = (
        unduplicated_data.sort_values("date").reset_index().drop("index", axis=1)
    )

    predicted_salary = unduplicated_data
    predicted_salary["key"] = "salary"

    ### needed to get the modal_salary. For calculating other income
    if predicted_salary.empty:
        modal_salary = 0
    else:
        modal_salary = predicted_salary["amount"].mode().values[0]

    return predicted_salary, modal_salary


def group_descriptions(descs):
    try:
        grouped_descs = []
        store = set()

        for i in range(len(descs)):
            similar_descs = []

            if descs[i] in store:
                continue

            for j in range(len(descs)):
                if descs[j] in store:
                    continue

                desc_i = descs[i].split()
                desc_j = descs[j].split()

                i_set = {word for word in desc_i}
                j_set = {word for word in desc_j}

                vector_space = i_set.union(j_set)

                i_vector = []
                j_vector = []

                for word in vector_space:
                    if word in i_set:
                        i_vector.append(1)
                    else:
                        i_vector.append(0)
                    if word in j_set:
                        j_vector.append(1)
                    else:
                        j_vector.append(0)

                dim_product = 0

                if sum(i_vector) != 0 and sum(j_vector) == 0:
                    continue

                if sum(i_vector) == 0:
                    if sum(j_vector) == 0:
                        similar_descs.append(descs[j])
                        store.add(descs[j])
                    continue

                for dim in range(len(vector_space)):
                    dim_product += i_vector[dim] * j_vector[dim]

                cosine_similarity = dim_product / float(
                    (sum(i_vector) * sum(j_vector)) ** 0.5
                )
                if cosine_similarity >= 0.67:
                    similar_descs.append(descs[j])
                    store.add(descs[j])

            grouped_descs.append(similar_descs)

    except KeyError as error:
        print(error)
        print("You need to pass the right key 'description',  to the grouping logic")
    else:
        return grouped_descs


def description_grouping_logic(id_credits):
    # stop_words = set(stopwords.words('english'))
    stop_words = {"atm", "from", "nip", "a", "of", "mobile", "frm"}
    #     lemma = WordNetLemmatizer()
    # tolist is faster than list(id_credits['description])
    descs = id_credits["description"].tolist()

    # Cleaning descriptions
    for i in range(len(descs)):
        descs[i] = re.sub(
            r"[-()\"#/&@;:<>{}+=~|.?,]", " ", str(descs[i])
        )  # Removing punctuation marks
        descs[i] = re.sub(r"  ", " ", str(descs[i]))  # Removing double spaces
        descs[i] = " ".join(
            [word for word in str(descs[i]).lower().split() if word not in stop_words]
        )  # Removing stop words
    #         descs[i] = " ".join(lemma.lemmatize(word) for word in descs[i].split()) # Using Lemmatizer

    # id_credits['cleaned_descs'] = descs

    grouped_descs = group_descriptions(descs)
    # Assigning descriptions to groups
    groups = []
    for desc in descs:
        for i in range(len(grouped_descs)):
            if desc in grouped_descs[i]:
                groups.append(i)

    id_credits["cosine_group"] = groups

    group_counts = Counter(
        groups
    )  # Number of times each group appeared in the bank statement

    repeated_groups = [
        group for group in group_counts.keys() if group_counts[group] > 1
    ]  # Groups that appear more than once

    return repeated_groups


def recurring_credits_logic(id_credits, statement_duration=None):
    credits = id_credits["amount"].tolist()
    credits_count = Counter(credits)
    recurring_credits = [
        credit
        for credit in credits_count.keys()
        if credits_count[credit] > 1 and credit >= 1000
    ]
    non_rec_group = len(recurring_credits)
    credit_group = []
    per = 5 / 100
    for i in range(len(credits)):
        found_group = False
        for j in range(len(recurring_credits)):
            low_range = recurring_credits[j] - (per * recurring_credits[j])
            high_range = recurring_credits[j] + (per * recurring_credits[j])

            if credits[i] >= low_range and credits[i] <= high_range:
                found_group = True
                credit_group.append(j)
                break

        if not found_group:
            credit_group.append(non_rec_group)
            non_rec_group += 1

    group_counts = Counter(credit_group)
    repeated_groups = [
        group for group in group_counts.keys() if group_counts[group] > 1
    ]
    id_credits["credit_group"] = credit_group

    return repeated_groups


def find_recurrency(df, statement_duration, logic):
    if (df["amount"] <= 900).sum() >= 1:
        return False

    # df.sort_values(by='date', inplace=True)
    credit_dates = list(df["date"])
    num_credits = len(credit_dates)
    start_date = min(credit_dates)
    end_date = max(credit_dates)
    first_month = (start_date.month, start_date.year)
    last_month = (end_date.month, end_date.year)

    credit_duration = (
        (last_month[0] - first_month[0]) + (12 * (last_month[1] - first_month[1])) + 1
    )

    total_repeats = num_credits - 1
    try:
        avg_tf = (end_date - start_date).days / total_repeats
        time_range = int(avg_tf * 0.4)
        periodic_repeats = 0
        for i in range(num_credits - 1):
            td = credit_dates[i + 1] - credit_dates[i]
            if td.days > avg_tf - time_range and td.days < avg_tf + time_range:
                periodic_repeats += 1

        credit_info = {}
        periodic_proba = (
            periodic_repeats / total_repeats
        ) * 100  # Probability of periodicity
        credit_info["periodic_probability"] = periodic_proba

        credit_spread = (credit_duration / statement_duration) * 100
        credit_info["credit_spread"] = credit_spread

        monthly_proba = (
            num_credits / statement_duration
        ) * 100  # Probability of the transaction happening every month
        credit_info["monthly_probability"] = monthly_proba
    except ZeroDivisionError:
        print("division by zero!")

    try:

        if logic == "dg":
            if credit_spread >= 55 and monthly_proba >= 55:
                return True
            else:
                return False

        else:
            if periodic_proba >= 70 and credit_spread >= 60 and monthly_proba >= 60:
                return True
            else:
                return False
    except TypeError:
        print("unsupported operand type(s), logic must be a string ")


def calculate_other_income(id_statement, predicted_salary):
    id_statement["date"] = pd.to_datetime(id_statement["date"])
    id_statement.sort_values(by="date", inplace=True)
    id_credits = id_statement[id_statement["type"] == "C"]

    start_date = id_statement["date"].min()
    end_date = id_statement["date"].max()

    first_month = (start_date.month, start_date.year)
    last_month = (end_date.month, end_date.year)

    statement_duration = (
        (last_month[0] - first_month[0]) + (12 * (last_month[1] - first_month[1])) + 1
    )

    repeated_groups = description_grouping_logic(id_credits)

    possible_income_statements = pd.DataFrame()

    for group in repeated_groups:
        group_statements = id_credits[id_credits["cosine_group"] == group]
        is_recurrent = find_recurrency(group_statements, statement_duration, logic="dg")

        if is_recurrent:
            possible_income_statements = pd.concat(
                [possible_income_statements, group_statements]
            )

    repeated_groups = recurring_credits_logic(id_credits, statement_duration=None)

    for group in repeated_groups:
        group_statements = id_credits[id_credits["credit_group"] == group]
        is_recurrent = find_recurrency(group_statements, statement_duration, logic="rc")

        if is_recurrent:
            possible_income_statements = pd.concat(
                [possible_income_statements, group_statements]
            )

    possible_income_statements = possible_income_statements[
        ~possible_income_statements.index.duplicated(keep="last")
    ]

    ### added this to David's logic. It just helps us to filter out unique other income predicted
    other_income = possible_income_statements

    if other_income.empty:
        predicted_other_income = pd.DataFrame(columns=id_statement.columns)
    else:
        predicted_other_income = other_income

    predicted_other_income["key"] = "other_income"

    #### I had to filter out the actual
    unique_predicted_other_income = predicted_other_income[
        ~predicted_other_income["amount"].isin(predicted_salary["amount"])
    ]

    ### needed to get the 70th percentile other income. For calculating other income
    if unique_predicted_other_income.empty:
        percentile_other_income = 0
    else:
        unique_predicted_other_income["date"] = pd.to_datetime(
            unique_predicted_other_income["date"]
        )
        ### get the date values
        unique_predicted_other_income["month"] = unique_predicted_other_income[
            "date"
        ].dt.month
        unique_predicted_other_income["month"] = unique_predicted_other_income[
            "month"
        ].apply(lambda x: str(x))

        ### get the year values
        unique_predicted_other_income["year"] = pd.to_datetime(
            unique_predicted_other_income["date"]
        ).dt.year
        unique_predicted_other_income["year"] = unique_predicted_other_income[
            "year"
        ].apply(lambda x: str(x))

        # ### concatenate both
        #### I had to do a groupby month and get the mean amount for each month.
        #### THat way, I'm able to get a sense of the mean amount coming in every month
        #### Afterwards, I found the 70th percentile of all mean combined together
        unique_predicted_other_income["month_year"] = unique_predicted_other_income[
            ["month", "year"]
        ].agg("/".join, axis=1)
        percentile_other_income = np.percentile(
            unique_predicted_other_income.groupby(["month_year"]).mean()["amount"], 70
        )

    unique_predicted_other_income = unique_predicted_other_income.reset_index().drop(
        "index", axis=1
    )

    return unique_predicted_other_income, percentile_other_income


def forecast_salary_day(salary_df):
    salary_df["date"] = pd.to_datetime(salary_df["date"])
    if salary_df.empty:
        return None

    salary_days = list(salary_df["date"].apply(lambda x: x.day))
    days_count = Counter(salary_days)
    max_occurence = max(days_count.values())

    if max_occurence == 1:
        return int(np.ceil(np.percentile(salary_days, 75)))

    expected_salary_day = 0
    for day in days_count.keys():
        if days_count[day] == max_occurence and day > expected_salary_day:
            expected_salary_day = day

    return expected_salary_day


def calculate_summary_info_on_income(data, forecasted_salary_day):

    try:
        data["day"] = data["date"].apply(lambda time: time.day)
        data["month"] = data["date"].apply(lambda time: time.month)

        data.loc[(data.day < 13) & (data.key == "salary"), "month"] -= 1

    except AttributeError:
        print(AttributeError)
        print("DataFrame object has no attribute KEY ")

    try:

        summary = {}

        if data.empty:
            ### when both logics didn't pick anything
            summary["salaryEarner"] = "No"
            summary["medianIncome"] = 0.0
            summary["averageOtherIncome"] = 0.0
            summary["expectedSalaryDay"] = None
            summary["lastSalaryDate"] = None
            summary["averageSalary"] = 0.0
            summary["confidenceIntervalonSalaryDetection"] = 0.0
            summary["salaryFrequency"] = None
            summary["numberSalaryPayments"] = 0
            summary["numberOtherIncomePayments"] = 0

            return summary

        else:

            ### Salary Earner
            if len(data[data["key"] == "salary"]) > 1:
                summary["salaryEarner"] = "Yes"
            else:
                summary["salaryEarner"] = "No"

            #### medianIncome
            if len(data[data["key"] == "salary"]) <= 1 and len(data[data["key"] == "other_income"]) == 0:
                summary["medianIncome"] = 0.0
            else:
                data["month"] = data["date"].dt.month
                data = data[data["key"].isin(["salary", "other_income"])]
                data["amount"] = data["amount"].astype(float)
                summary["medianIncome"] = (
                    data.groupby("month")["amount"].median().median()
                )
                summary["medianIncome"] = round(float(summary["medianIncome"]), 2)

            #### averageOtherIncome
            if len(data[data["key"] == "other_income"]) <= 0:
                summary["averageOtherIncome"] = 0.0
            else:
                other_income_data = data[data["key"] == "other_income"]
                other_income_data["amount"] = other_income_data["amount"].astype(float)
                summary["averageOtherIncome"] = np.mean(
                    other_income_data.groupby("month")["amount"].mean()
                )
                summary["averageOtherIncome"] = round(
                    float(summary["averageOtherIncome"]), 2
                )

            #### latestSalaryDate
            if len(data[data["key"] == "salary"]) <= 0:
                summary["lastSalaryDate"] = None
            else:
                summary["lastSalaryDate"] = str(
                    data[data["key"] == "salary"]["date"].iloc[-1].date()
                )

            #### averageSalary
            if len(data[data["key"] == "salary"]) <= 1:
                summary["averageSalary"] = 0.0
            else:
                ### Now, I'm finding the mean of all mean salary amounts recieved monthly.
                data["month"] = data["date"].dt.month
                summary["averageSalary"] = round(
                    np.mean(
                        data[data["key"] == "salary"].groupby("month")["amount"].mean()
                    ),
                    2,
                )
                summary["averageSalary"] = round(float(summary["averageSalary"]), 2)

            #### confidenceIntervalonSalaryDetection
            if len(data[data["key"] == "salary"]) <= 1:
                summary["confidenceIntervalonSalaryDetection"] = 0
            else:
                data["month"] = pd.to_datetime(data["date"]).dt.month
                unique_month = data["month"].nunique()
                average_salary = round(
                    np.mean(
                        data[data["key"] == "salary"].groupby("month")["amount"].mean()
                    ),
                    2,
                )
                standard_deviation = np.std(data[data["key"] == "salary"]["amount"])
                summary["confidenceIntervalonSalaryDetection"] = np.round(
                    (
                        1
                        - (standard_deviation / average_salary)
                        - min(
                            1 - (standard_deviation / average_salary),
                            (1 / unique_month),
                        )
                    ),
                    2,
                )

            ### salaryFrequency
            print("no of salary transactions: ", len(data[data["key"] == "salary"]))
            if len(data[data["key"] == "salary"]) <= 0:
                summary["salaryFrequency"] = None
            elif (
                max(
                    pd.to_datetime(
                        data[data["key"] == "salary"]["date"]
                    ).dt.month.value_counts()
                )
                == 1
            ):
                summary["salaryFrequency"] = "1"
            elif (
                max(
                    pd.to_datetime(
                        data[data["key"] == "salary"]["date"]
                    ).dt.month.value_counts()
                )
                > 1
            ):
                summary["salaryFrequency"] = ">1"

            print("salaryFrequency: ", summary["salaryFrequency"])
            print("salaryEarner: ", summary["salaryEarner"])

            #### numberSalaryPayments
            if len(data[data["key"] == "salary"]) <= 0:
                summary["numberSalaryPayments"] = 0
            else:
                salary_transactions = data[data["key"] == "salary"]
                summary["numberSalaryPayments"] = len(salary_transactions)

            #### numberOtherIncomePayments
            if len(data[data["key"] == "other_income"]) <= 0:
                summary["numberOtherIncomePayments"] = 0
            else:
                other_income = data[data["key"] == "other_income"]
                summary["numberOtherIncomePayments"] = len(other_income)

            #### expectedSalaryDay
            if len(data[data["key"] == "salary"]) <= 1:
                summary["expectedSalaryDay"] = None
            else:
                summary["expectedSalaryDay"] = forecasted_salary_day
        return summary

    except KeyError:
        print(KeyError)
        print(
            "dataframe does not have salary as a keyword, pass in the combined dataframe"
        )


def calculate_summary_on_time_period(data):
    summary = {}

    if data.empty:
        ### when both logics didn't pick anything
        summary = summary
        summary["noOfTransactingMonths"] = 0
        summary["monthPeriod"] = 0
        summary["yearInStatement"] = 0
        summary["firstDay"] = 0
        summary["lastDay"] = 0
    else:

        data["month"] = pd.to_datetime(data["date"]).dt.month
        data["month"] = data["month"].apply(lambda x: str(x))

        #### noOfMonths
        ### get the years
        data["year"] = pd.to_datetime(data["date"]).dt.year
        data["year"] = data["year"].apply(lambda x: str(x))
        ### concatenate both
        data["month_year"] = data[["month", "year"]].agg("/".join, axis=1)
        summary["noOfTransactingMonths"] = data["month_year"].nunique()

        #### monthPeriod
        first_month = pd.to_datetime(data["date"].min()).month_name()

        last_month = pd.to_datetime(data["date"].max()).month_name()

        summary["monthPeriod"] = " - ".join([first_month, last_month])

        #### year
        if len(data["year"].unique()) <= 1:
            summary["yearInStatement"] = "".join(data["year"].unique())
        else:
            summary["yearInStatement"] = ", ".join(data["year"].unique())

        #### first_day
        summary["firstDay"] = str(pd.to_datetime(data["date"].min()).date())

        #### last_day
        summary["lastDay"] = str(pd.to_datetime(data["date"].max()).date())

    return summary


def cash_info_on_amount(data, pivot="M"):
    """
    Func takes in a path and calculates cash summary info on amount from a bank statement
    """
    data = get_date(data)

    if len(data) <= 0:
        return None

    credit = data[data.type == "C"]
    debit = data[data.type == "D"]
    # Avertage  Credits
    average_credit = credit.set_index("date")
    if len(credit["amount"]) <= 0:
        average_credit = 0.0
    else:
        average_credit = round(
            float(
                average_credit.groupby(pd.Grouper(freq=pivot)).mean()["amount"].mean()
            ),
            2,
        )
    # Average  Debit
    average_debit = debit.set_index("date")
    if len(debit["amount"]) <= 0:
        average_debit = 0.0
    else:
        average_debit = round(
            float(
                average_debit.groupby(pd.Grouper(freq=pivot)).mean()["amount"].mean()
            ),
            2,
        )

    total_credit_turn_over = credit.groupby(["month"]).amount.sum()
    total_credit_turn_over = float(round(total_credit_turn_over.sum(), 2))
    # total_debit_turnover
    total_debit_turn_over = debit.groupby(["month"]).amount.sum()
    total_debit_turn_over = float(round(total_debit_turn_over.sum(), 2))
    average_balance = 0.0
    closing_balance = 0.0
    if "balance" in data.keys() and pd.isnull(data["balance"]).sum() == 0:
        data["balance"] = pd.to_numeric(data["balance"])
        # average_balance
        average_balance = data.set_index("date")
        if len(data["balance"]) <= 0:
            average_balance = 0.0
            closing_balance = 0.0
        else:
            # average_balance
            average_balance = round(
                float(
                    average_balance.groupby(pd.Grouper(freq=pivot))
                    .mean()["balance"]
                    .mean()
                ),
                2,
            )
            # closing_balance
            closing_balance = round(float(list(data["balance"])[-1]), 2)

    dic = {
        "averageCredits": average_credit,
        "averageDebits": average_debit,
        "totalCreditTurnover": total_credit_turn_over,
        "totalDebitTurnover": total_debit_turn_over,
        "averageBalance": average_balance,
        "closingBalance": closing_balance,
    }

    return dic


def calculate_inflow_outflow_rate(data):

    credit_transactions = data[data["type"] == "C"]
    debit_transactions = data[data["type"] == "D"]

    credit_sum = credit_transactions["amount"].sum()
    debit_sum = debit_transactions["amount"].sum()

    inflowOutflowRate = round(credit_sum - debit_sum, 2)

    if inflowOutflowRate == 0:
        cash_flow = "Equal credit to debit"
    elif inflowOutflowRate < 0:
        cash_flow = "Negative Cash Flow"
    else:
        cash_flow = "Positive Cash Flow"

    return cash_flow


def getTopTransferAccount(data):

    remove_bad_narrations = data[
        ~data["description"].str.contains(r"(xxxxxxxxxx|xxxxxxx|########|xxxxxxxx)")
    ]

    new_data = remove_bad_narrations

    # 8696086, 8730008, 1076867, 41180430, 59399147, 44594665

    list_stopwords = set(stop_words.get_stop_words("en"))
    # nltk_words = list(nltk.corpus.stopwords.words('english'))
    # list_stopwords.extend(nltk_words)
    new_data["description"] = new_data["description"].str.lower()
    new_data["description"] = new_data["description"].str.rstrip()
    new_data["description"] = new_data["description"].str.lstrip()
    new_data["description"] = new_data["description"].apply(
        lambda x: " ".join(re.split(";|,|:|/|@|-|=|_|#", str(x)))
    )

    new_data["description"] = new_data["description"].apply(
        lambda x: " ".join([word for word in x.split() if word not in (list_stopwords)])
    )

    ### filter out transactions with the "transfer" keyword
    debit_transactions = new_data[new_data.type == "D"]
    filter_by_amount = debit_transactions[(debit_transactions["amount"] > 2100)]
    filter_by_transfer_keyword = filter_by_amount[
        filter_by_amount["description"].str.contains(r"(transfer)")
    ]

    if filter_by_transfer_keyword.empty:
        ### this condition checks if there are no transactions with the "transfer" keyword
        result = "no top transfer account found"
    else:
        ### the code line below splits by transfer keywords and returns left and right pairs
        splitName = re.split(
            "transfer ", str(filter_by_transfer_keyword["description"].mode().values[0])
        )

        ### the code line below checks if the last occuring string is transfer
        ### It also checks if there is only string after the transfer kwyword and the string is a combination of digit
        ### third condition double checks if we have something like 'unionkorrect transfer'. i.e. len of returned list is 1
        if (
            splitName[-1] == ("transfer")
            or len(re.findall("[1-9]", str(splitName[-1]))) > 0
            or len(splitName) == 1
        ):
            result = "transfer is the either last keyword or the last keyword is non-alphabeth"
        else:
            ### the code line below splits all corresponding strings after the "transfer" keywords separated by comma
            splitName = splitName[1].split(" ")
            ### the code line below removes all non-alphabets strings or digits
            strings_cleaned = str(
                ",".join(re.findall("[a-zA-Z]+", str(splitName)))
            ).split(",")
            ### the function below checks if there's just a single alphabetic string after the "transfer" keyword.
            ### Then it assigns the second_string as empty string
            if len(strings_cleaned) <= 1:
                first_string = strings_cleaned[0]
                second_string = ""
                result = first_string + "" + second_string
            ### the function below checks if the string after "transfer" keyword is a single char like "e" or "m"
            ### If true, then it assigns the second string after "transfer" keyword as the first_string and the third string after the "transfer" keyword as second_string
            ### else, the first string after "transfer" is assigned as first_string and the second string as second_string
            elif len(strings_cleaned) <= 2:
                if len(strings_cleaned[0]) <= 2:
                    first_string = strings_cleaned[1]
                    second_string = strings_cleaned[2]
                else:
                    first_string = strings_cleaned[0]
                    second_string = strings_cleaned[1]
            else:
                first_string = strings_cleaned[0]
                second_string = strings_cleaned[1]

            result = first_string + " " + second_string

    return result


def identify_gambling_transactions(data):

    list_stopwords = set(stop_words.get_stop_words("en"))
    # nltk_words = list(nltk.corpus.stopwords.words('english'))
    # list_stopwords.extend(nltk_words)

    data["description"] = data["description"].str.lower()
    data["description"] = data["description"].str.rstrip()
    data["description"] = data["description"].str.lstrip()
    data["description"] = data["description"].apply(
        lambda x: " ".join(re.split(";|,|:|/|@|-|=|_|#", str(x)))
    )

    data["description"] = data["description"].apply(
        lambda x: " ".join([word for word in x.split() if word not in (list_stopwords)])
    )

    debit_transactions = data[data["type"] == "D"]
    debit_transactions["description"] = debit_transactions["description"].str.lower()
    debit_transactions = debit_transactions.sort_values(["nuban", "date", "amount"])
    debit_transactions = debit_transactions.dropna(subset=["description"])
    debit_transactions = debit_transactions.reset_index().drop("index", axis=1)

    check_gambling = debit_transactions[
        debit_transactions["description"].str.contains(
            r"(mybet9ja|bett|nairabet|bet9|betway|22bet|bet365|1xbet|sporty|betwinner|bet9ja\
                                        |betfair|betkin|lottery|betking|betway|betting|bet 9ja|bet naija|betty\
                                        |sportybet|merrybet|betpaw|alatbet9ja|betnaija|paripesabet|melbet|betwinner\
                                        |888sport|wazobet|irokobet|cyberbet|bangbet|doublebet|winnersgoldenbet\
                                        |lionsbet|accessbet|naijabet|surebet|supabets|1960bet|fortunebet|betwin9ja\
                                        |lovinbet)"
        )
    ]

    if len(check_gambling) == 0:
        status = "No Gambling Transactions Found"
    else:
        status = "Gambling Transactions Found"

    return status


def calculate_gambling_rate(data):

    list_stopwords = set(stop_words.get_stop_words("en"))

    data["description"] = data["description"].str.lower()
    data["description"] = data["description"].str.rstrip()
    data["description"] = data["description"].str.lstrip()
    data["description"] = data["description"].apply(
        lambda x: " ".join(re.split(";|,|:|/|@|-|=|_|#", str(x)))
    )

    data["description"] = data["description"].apply(
        lambda x: " ".join([word for word in x.split() if word not in (list_stopwords)])
    )

    credit_transactions = data[data["type"] == "C"]
    debit_transactions = data[data["type"] == "D"]

    ### not using the bet keyword because it'll capture debit transactions with narrations such as: union beta, elizabeth, herbet, ogbete, sunbeth
    ### had to get some bet keywords by researching for bet company names online
    check_gambling = debit_transactions[
        debit_transactions["description"].str.contains(
            r"(mybet9ja|bett|nairabet|bet9|betway|22bet|bet365|1xbet|sporty|betwinner|bet9ja\
                                        |betfair|betkin|lottery|betking|betway|betting|bet 9ja|bet naija|betty\
                                        |sportybet|merrybet|betpaw|alatbet9ja|betnaija|paripesabet|melbet|betwinner\
                                        |888sport|wazobet|irokobet|cyberbet|bangbet|doublebet|winnersgoldenbet\
                                        |lionsbet|accessbet|naijabet|surebet|supabets|1960bet|fortunebet|betwin9ja\
                                        |lovinbet)"
        )
    ]

    sum_gambling = check_gambling["amount"].sum()
    sum_inflow = credit_transactions["amount"].sum()
    try:
        gambling_rate = sum_gambling / sum_inflow
    except ZeroDivisionError:
        print("division by zero!")
    else:
        return round(gambling_rate, 2)


def identify_other_loan_amounts(data):

    list_stopwords = set(stop_words.get_stop_words("en"))
    # nltk_words = list(nltk.corpus.stopwords.words('english'))
    # list_stopwords.extend(nltk_words)

    data["description"] = data["description"].str.lower()
    data["description"] = data["description"].str.rstrip()
    data["description"] = data["description"].str.lstrip()
    data["description"] = data["description"].apply(
        lambda x: " ".join(re.split(";|,|:|/|@|-|=|_|#", str(x)))
    )

    data["description"] = data["description"].apply(
        lambda x: " ".join([word for word in x.split() if word not in (list_stopwords)])
    )

    debit_transactions = data[data["type"] == "D"]
    debit_transactions = debit_transactions.sort_values(["nuban", "date", "amount"])
    debit_transactions = debit_transactions.dropna(subset=["description"])
    debit_transactions = debit_transactions.reset_index().drop("index", axis=1)

    check_loan = debit_transactions[
        debit_transactions["description"].str.contains(
            r"(loan repayment|loan|loan payment|fairmoney|renmoney|palmcredit\
                                        |paycredit|kwikmoney|rpmt microloan|repayments|loanfullyrepaid|repaidloan|loanpartlyrepaid\
                                        |loan rept|loan kwikcash|csloan|microloan|loan kwikcashlan|z700 retail loan|retail loan\
                                        |loan kwikcashlang|loan onefi|cdl loans|z716 retail loan|loan payoff|loan recovery\
                                        |sokoloan|loan repymt|loans|naijaloan|alat loan|loan repay|kwikbet247)"
        )
    ]
    #
    total_loan_amount = float(check_loan["amount"].sum())
    return round(total_loan_amount, 2)


def recycling_flag(statement):
    if len(statement) <= 1:
        return False, 0

    credits = statement.loc[(statement["type"] == "C") & (statement["amount"] > 1000)]
    debits = statement.loc[(statement["type"] == "D") & (statement["amount"] > 1000)]
    sweep_count = 0
    debit_sweeps = set()
    sweep_amount = 0

    credit_count = len(statement[statement["type"] == "C"])

    if credit_count == 0:
        return False, 0

    for i in credits.index:
        credit_amount = credits.loc[i, "amount"]
        credit_date = credits.loc[i, "date"]

        debits_after = debits.loc[
            (debits["date"] >= credit_date)
            & (debits["date"] <= credit_date + timedelta(days=7))
            & (debits["amount"] >= credit_amount * 0.95)
            & (debits["amount"] <= credit_amount * 1.05)
        ]

        sim_index = debit_sweeps.intersection(set(debits_after.index))
        debits_after.drop(index=sim_index, inplace=True)

        if len(debits_after) > 0:
            sweep_index = debits_after.index[0]
            debit_sweeps.add(sweep_index)
            sweep_amount += debits_after.loc[sweep_index, "amount"]
            sweep_count += 1

    if (sweep_count / credit_count) >= 0.5:
        return True, sweep_amount
    else:
        return False, 0


def sweep_flag(statement):
    if not set(statement.columns) >= {"balance"}:
        return False

    if pd.isnull(statement["balance"]).sum() > 0:
        return False

    if len(statement) <= 1:
        return True

    per = 20 / 100
    statement_duration = (statement["date"].max() - statement["date"].min()).days

    if statement_duration == 0:
        return True

    statement["end_date"] = (statement["date"].to_list())[1:] + [
        statement.iloc[-1]["date"]
    ]
    statement["td"] = statement["end_date"] - statement["date"]
    statement["td"] = statement["td"].apply(lambda x: x.days)

    balances = np.array(statement["balance"])
    bal_ranges = []

    while len(balances) != 0:
        low_range = balances[0] - (per * balances[0])
        high_range = balances[0] + (per * balances[0])
        bal_ranges.append(balances[0])
        b = balances[balances >= low_range]
        b = b[b <= high_range]
        balances = np.setdiff1d(balances, b)

    balance_dict = {balance: 0 for balance in bal_ranges}

    for balance in balance_dict.keys():
        low_range = balance - (per * balance)
        high_range = balance + (per * balance)

        balance_df = statement.loc[
            (statement["balance"] >= low_range) & (statement["balance"] <= high_range)
        ]

        balance_dict[balance] = balance_df["td"].sum()

    max_timeframe = max(balance_dict.values())

    if max_timeframe / statement_duration < 0.65:
        return False

    else:
        return True


def find_recurring_expenses(id_statement):
    if len(id_statement) <= 1:
        return (
            pd.DataFrame(columns=id_statement.columns),
            {"hasRecurringExpense": "No", "averageRecurringExpense": 0.0},
        )

    id_statement["date"] = pd.to_datetime(id_statement["date"])
    id_statement.sort_values(by="date", inplace=True)
    id_debits = id_statement[id_statement["type"] == "D"]

    start_date = id_statement["date"].min()
    end_date = id_statement["date"].max()

    first_month = (start_date.month, start_date.year)
    last_month = (end_date.month, end_date.year)

    statement_duration = (
        (last_month[0] - first_month[0]) + (12 * (last_month[1] - first_month[1])) + 1
    )

    repeated_groups = description_grouping_logic(id_debits)

    recurring_expenses = pd.DataFrame()

    for group in repeated_groups:
        group_statements = id_debits[id_debits["cosine_group"] == group]
        is_recurrent = find_recurrency(group_statements, statement_duration, logic="dg")

        if is_recurrent:
            recurring_expenses = pd.concat([recurring_expenses, group_statements])

    if len(recurring_expenses) == 0:
        return (
            pd.DataFrame(columns=id_statement.columns),
            {"hasRecurringExpense": "No", "averageRecurringExpense": 0.0},
        )

    id_debits["recurring_expense"] = 0.0
    id_debits.loc[recurring_expenses.index, "recurring_expense"] = recurring_expenses[
        "amount"
    ]

    id_debits.set_index("date", inplace=True)
    avg_recurring_expenses = round(
        id_debits.groupby(pd.Grouper(freq="M")).sum()["recurring_expense"].mean(), 2
    )

    return (
        recurring_expenses,
        {
            "hasRecurringExpense": "Yes",
            "averageRecurringExpense": avg_recurring_expenses,
        },
    )


def get_date(data):
    """
    The function takes the original transaction table and creates a datatime columns
    """
    # data["Transaction Date"] = pd.to_datetime(data["Transaction Date"])
    if len(data) <= 0:
        return None
    else:
        data = data.copy()

        data["day"] = data["date"].apply(lambda time: time.day)
        data["month"] = data["date"].apply(lambda time: time.month)
        data["week"] = data["date"].apply(lambda time: time.week)
        data["week_of_month"] = data["day"].apply(lambda day: (day - 1) // 7 + 1)
        dmap = {
            1: "January",
            2: "Febuary",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December",
        }
        data["month"] = data["month"].map(dmap)
        data = (
            data.sort_values("date", ascending=True).reset_index().drop("index", axis=1)
        )

    return data


def get_transaction_pattern_analysis(data, recurring_expenses_df):

    """The function takes a dataframe and outputs a dict of statistical variable e.g
        datetime and transaction over a given period of time. """

    summary = {}

    if data.empty:
        summary["lastCreditDate"] = 0
        summary["lastDebitDate"] = 0
        summary["highestMAWOfCredit"] = 0
        summary["highestMAWOfDebit"] = 0
        summary["MAWWZeroBalanceInAccount"] = 0
        summary["transactionsLess10000"] = 0
        summary["transactionsBetween10000And100000"] = 0
        summary["transactionsBetween100000And500000"] = 0
        summary["transactionsGreater500000"] = 0
        summary["recurringExpense"] = 0
        summary["NODWBalanceLess5000"] = 0
        summary["mostFrequentBalanceRange"] = 0
        summary["mostFrequentTransactionRange"] = 0

        return summary

    else:
        recurring_expenses_df["amount"] = recurring_expenses_df["amount"].apply(
            lambda x: round(float(x), 2)
        )
        zero_balance = 0
        top_3_expense = 0
        if len(recurring_expenses_df) < 1:

            top_3_expense = {}
        elif (
            len(recurring_expenses_df.cosine_group.unique()) == 2
            or len(recurring_expenses_df.cosine_group.unique()) == 1
        ):
            top_3_expense = (
                recurring_expenses_df.groupby("cosine_group")
                .apply(lambda x: x.loc[x["amount"].eq(x["amount"].mode()[0])].tail(1))
                .reset_index(drop=True)[["description", "amount"]]
                .to_dict("records")
            )
        else:
            df = recurring_expenses_df.groupby("cosine_group").apply(
                lambda x: x.loc[x["amount"].eq(x["amount"].mode()[0])]
            )
            # retieve the index of the value counts
            cosine_group_value = df["cosine_group"].value_counts().index
            # get the fist 3 values  from the value counts (highest 3 values)
            top3 = list(cosine_group_value)[:3]
            # filter your dataframe using the top 3 values on the cosine_group column
            df = df[df["cosine_group"].isin(top3)]

            group_expense = df[["description", "amount", "cosine_group"]].reset_index(
                drop=True
            )
            group_expense = group_expense.copy()
            # groupby the cosine_group and extract the first value
            top_3_expense = (
                group_expense.groupby(["cosine_group"]).first().to_dict("records")
            )

        credit_df = data[data.type == "C"]
        debit_df = data[data.type == "D"]
        #### lastCreditDate
        if len(credit_df["date"]) <= 0:
            last_credit_date = None
        else:
            last_credit_date = str(pd.to_datetime(credit_df["date"].max()).date())
        #### lastDebitDate
        if len(debit_df["date"]) <= 0:
            last_debit_date = None
        else:
            last_debit_date = str(pd.to_datetime(debit_df["date"].max()).date())

        # last_debit_date = str(pd.to_datetime(debit_df['date'].max()).date())
        max_credit = credit_df["amount"].max()
        max_debit = debit_df["amount"].max()
        credit_list = credit_df[credit_df["amount"] == max_credit][
            ["week_of_month", "month"]
        ].to_dict("records")
        debit_list = debit_df[debit_df["amount"] == max_debit][
            ["week_of_month", "month"]
        ].to_dict("records")
        # calculate highestMAWOfCredit
        highestMAWOfCredit = dict(ChainMap(*credit_list))
        # calculate highestMAWOfCredit
        highestMAWOfDebit = dict(ChainMap(*debit_list))
        if "balance" in data.keys() and pd.isnull(data["balance"]).sum() == 0:
            MAWWZeroBalanceInAccount = data[data["balance"] == zero_balance][
                ["week_of_month", "month"]
            ].to_dict("records")

            if len(MAWWZeroBalanceInAccount) >= 1:

                MAWWZeroBalanceInAccount = MAWWZeroBalanceInAccount[0]
            else:
                MAWWZeroBalanceInAccount = {}

            # calculate NoDaysWithLowBalance_less_5000
            NoDaysWithLowBalance_less_5000 = data[data["balance"] < 50000].date.nunique(
                dropna=True
            )
        else:
            MAWWZeroBalanceInAccount = {}
            NoDaysWithLowBalance_less_5000 = 0

        #####transaction binning#######
        tran_data = data.copy()
        bins = [-np.inf, 10000, 100000, 500000, np.inf]
        # create label for trans range classisfication
        labels = [
            "transactionsLess10000",
            "transactionsBetween10000And100000",
            "transactionsBetween100000And500000",
            "transactionsGreater500000",
        ]
        # create a dataframe with new column 'bin', which holds the transaction range
        tran_data["bins"] = pd.cut(
            tran_data.amount, bins=bins, labels=labels, right=False, include_lowest=True
        )
        transaction_binning = tran_data.bins.value_counts().to_dict()
        # mostFrequentBalanceRange
        if "balance" in data.keys() and pd.isnull(data["balance"]).sum() == 0:
            bins = [-np.inf, 10000, 100000, 500000, np.inf]
            labels = ["< 10,000", "10,000 - 100,000", "100,000 - 500,000", "> 500,000"]
            tran_data["balance_bins"] = pd.cut(
                tran_data.balance,
                bins=bins,
                labels=labels,
                right=False,
                include_lowest=True,
            )
            mostFrequentBalanceRange = tran_data["balance_bins"].value_counts().idxmax()

        else:
            mostFrequentBalanceRange = 0

        # mostFrequentTransactionRange
        transmap = {
            "transactionsLess10000": "< 10,000",
            "transactionsBetween10000And100000": "10,000 - 100,000",
            "transactionsBetween100000And500000": "100,000 - 500,000",
            "transactionsGreater500000": "> 500,000",
        }
        tran_data["bins"] = tran_data["bins"].map(transmap)
        mostFrequentTransactionRange = tran_data["bins"].value_counts().idxmax()

        date_variables = {
            "lastDateOfCredit": last_credit_date,
            "lastDateOfDebit": last_debit_date,
            "highestMAWOCredit": highestMAWOfCredit,
            "highestMAWODebit": highestMAWOfDebit,
            "MAWWZeroBalanceInAccount": MAWWZeroBalanceInAccount,
            "NODWBalanceLess5000": NoDaysWithLowBalance_less_5000,
            "mostFrequentBalanceRange": mostFrequentBalanceRange,
            "mostFrequentTransactionRange": mostFrequentTransactionRange,
            "recurringExpense": top_3_expense,
        }
        # merge date_variables and transaction_binning
        date_variables.update(transaction_binning)

    return date_variables


def net_average_monthly_earnings(
    id_credits, average_expenses, averageOtherIncome, averageSalary
):

    if len(id_credits) <= 0:
        return None

    netAverageMonthlyEarnings = (averageOtherIncome + averageSalary) - average_expenses

    dic = {"netAverageMonthlyEarnings": float(round(netAverageMonthlyEarnings, 2))}

    return dic


def account_activity(statement):

    data = statement.copy()
    if len(data) <= 0:
        return None

    set_stopwords = set(stop_words.get_stop_words("en"))
    #     lemma = WordNetLemmatizer()
    # tolist is faster than list(id_credits['description])
    descs = data["description"].tolist()

    # Cleaning descriptions
    for i in range(len(descs)):
        descs[i] = re.sub(
            r"[-()\"#/&@;:<>{}+=~|.?,]", " ", str(descs[i])
        )  # Removing punctuation marks
        descs[i] = re.sub(r"  ", " ", descs[i])  # Removing double spaces
    #         descs[i] = ' '.join([word for word in descs[i].lower().split() if word not in stop_words]) # Removing stop words

    data["description"] = descs
    data["description"] = data["description"].apply(
        lambda x: " ".join([word for word in x.split() if word not in (set_stopwords)])
    )

    # filter transsaction above >= 100
    transactions = data[data.amount >= 100]
    transactions = transactions.dropna(subset=["description"])
    transactions = transactions.reset_index().drop("index", axis=1)
    # filter transaction not(listed keywords)
    transactions_df = transactions[
        ~transactions["description"].str.contains(
            r"\b(?:transfer levy|alert|tax charges|charges fee|vat|transaction charge|withholding tax|mybankstatement\
                                                                          |transfer commission|stamp duty|crd iss fee|card fee|maintenance|time charge|penalchg|credit card repayment\
                                                                          |code charge|form charge|visacard|mastercard|vervecard|statement charge|stmnt chrg|form charge\
                                                                          |session fee|token|sms|service chgres|handling charges|maint|elect money trsf|fip charges|fip chrgs|bal charge\
                                                                          |service charge|tax charges|nacs charges|statement printing charge|deposit charge|neft transfer charges\
                                                                          |issuance fee|chq charges|session time charge|charge salary|bvn|overdrawn interest|trf fee|mtrf fee|mob pymt fee\
                                                                          |ussd paybills|cheque charge|session charge|custodian charge|cheque book charge|chq issue charge|stmt\
                                                                          |verve|issuance fee|chqbk fee|wd fee|insurance fee|visa|fee charge|manage fee|fee pymt|bankstatement)\b",
            na=False,
        )
    ]

    # here, I'm trying to extract the unique days in the bank statemments. Transactions that occured more than once are counted as a single transaction.
    transactions_df["unique_transaction_day"] = transactions_df.apply(
        lambda x: str(x["date"].day) + "/" + str(x["date"].month), axis=1
    )

    # no_trans_days = transactions_df.date.nunique()    ## we can do away with this.
    trans_dates = list(data["date"])
    start_date = min(trans_dates)
    end_date = max(trans_dates)

    try:
        # act_activity = no_trans_days / (end_date - start_date).days ## we can do away with this
        act_activity = (
            transactions_df["unique_transaction_day"].nunique()
            / (end_date - start_date).days
        )
    except ZeroDivisionError:
        # print("division by zero!")
        return {"accountActivity": 0}

    else:
        dic = {"accountActivity": round(act_activity, 1)}
        return dic


def get_expense_categories(statement, keywords):
    debits = statement[statement["type"] == "D"]

    if len(debits) == 0:
        expense_categories = {}
        for category in [
            "bills",
            "religiousGiving",
            "clubsAndBars",
            "gambling",
            "utilitiesAndInternet",
            "cableTv",
            "airtime",
            "bankCharges",
        ]:
            expense_categories[category] = 0.0

        return expense_categories, 0.0

    debits["unique_months"] = debits.apply(
        lambda x: str(x["date"].year) + "-" + str(x["date"].month), axis=1
    )

    debits["description"] = debits["description"].str.lower()
    debits["description"] = debits["description"].apply(
        lambda x: re.sub(r"[-()\"#/&@;:<>{}+=~|.?,]", " ", x)
    )
    debits = debits[~debits["description"].str.contains("atm")]

    debits.sort_values(by="date", inplace=True)

    expense_categories = {}
    debits["is_expense"] = False

    for category in [
        "bills",
        "religiousGiving",
        "clubsAndBars",
        "gambling",
        "utilitiesAndInternet",
        "cableTv",
        "airtime",
        "bankCharges",
    ]:
        debits[category] = 0.0
        category_keywords = keywords[keywords["category"] == category][
            "keyword"
        ].to_list()
        category_debits = debits[
            debits["description"].str.contains("|".join(category_keywords))
        ]

        debits.loc[category_debits.index, category] = category_debits["amount"]
        debits.loc[category_debits.index, "is_expense"] = True

        ## check sum for each category. then divide by unique count of transacting months.
        ## The conditional statement helps us return a 0 whenever a category doesnt have any data
        if len(debits[debits[category] != 0]) > 0:
            expense_categories[category] = round(
                debits[debits[category] != 0][category].sum()
                / debits[debits[category] != 0]["unique_months"].nunique(),
                2,
            )
        else:
            expense_categories[category] = 0

    ## total debit transactions / number of months
    avg_expenses = round(
        float(debits["amount"].sum() / debits["unique_months"].nunique()), 2
    )

    return expense_categories, avg_expenses


def get_expense_channels(statement, keywords):
    debits = statement[statement["type"] == "D"]

    if len(debits) == 0:
        expense_channels = {}
        for channel in [
            "atmWithdrawalsSpend",
            "webSpend",
            "posSpend",
            "ussdTransactions",
            "spendOnTransfers",
            "internationalTransactionsSpend",
        ]:
            expense_channels[channel] = 0.0

        return expense_channels

    debits["unique_months"] = debits.apply(
        lambda x: str(x["date"].year) + "-" + str(x["date"].month), axis=1
    )

    debits.dropna(subset=["description"], inplace=True)
    debits["description"] = debits["description"].astype(str)
    debits["description"] = debits["description"].str.lower()
    debits["description"] = debits["description"].apply(
        lambda x: re.sub(r"[-()\"#/&@;:<>{}+=~|.?,]", " ", str(x))
    )

    expense_channels = {}
    for channel in [
        "atmWithdrawalsSpend",
        "webSpend",
        "posSpend",
        "ussdTransactions",
        "spendOnTransfers",
        "internationalTransactionsSpend",
    ]:
        debits[channel] = 0.0
        channel_keywords = keywords[keywords["category"] == channel][
            "keyword"
        ].to_list()
        channel_debits = debits[
            debits["description"].str.contains("|".join(channel_keywords))
        ]

        debits.loc[channel_debits.index, channel] = channel_debits["amount"]

        ## check sum for each channel. then divide by unique count of transacting months
        ## The conditional statement helps us return a 0 whenever a category doesnt have any data
        if len(debits[debits[channel] != 0]) > 0:
            expense_channels[channel] = round(
                debits[debits[channel] != 0][channel].sum()
                / debits[debits[channel] != 0]["unique_months"].nunique(),
                2,
            )
        else:
            expense_channels[channel] = 0

    return expense_channels


def get_inflow_outflow_rate(statement):
    if len(statement) == 0:
        return "Neutral Cash Flow"

    data = statement.copy()
    data.set_index("date", inplace=True)

    debits = data[data["type"] == "D"]
    credits = data[data["type"] == "C"]

    if len(debits) == 0:
        return "Positive Cash Flow"
    if len(credits) == 0:
        return "Negative Cash Flow"

    monthly_debits = debits.groupby(pd.Grouper(freq="M")).sum()
    monthly_credits = credits.groupby(pd.Grouper(freq="M")).sum()

    monthly_debits.rename(columns={"amount": "debit_amount"}, inplace=True)
    monthly_credits.rename(columns={"amount": "credit_amount"}, inplace=True)

    merged_df = pd.concat(
        [monthly_debits["debit_amount"], monthly_credits["credit_amount"]], axis=1
    )

    merged_df.fillna(0.0, inplace=True)

    cashflow = (merged_df["credit_amount"] - merged_df["debit_amount"]).to_list()

    positives = 0
    negatives = 0
    for i in range(len(cashflow)):
        if cashflow[i] > 0:
            positives += 1
        elif cashflow[i] < 0:
            negatives += 1

    if positives > negatives:
        return "Positive Cash Flow"
    elif negatives > positives:
        return "Negative Cash Flow"
    else:
        return "Neutral Cash Flow"


def get_account_name(desc, search_list):
    name = None
    for word in search_list:
        split_desc = desc.split(word)
        if len(split_desc) > 1:
            name = split_desc[1]
    if name:
        name = name.split(" ")
        if len(name) == 1:
            name = name[0]
        else:
            name = name[0] + " " + name[1]

    name = name.strip()

    try:
        has_date = parse(name, fuzzy=True)
        return None
    except:
        if name == "":
            return None
        else:
            return name.title()


def get_top_recipient_account(statement):
    debits = statement[statement["type"] == "D"]
    debits = debits[debits["description"].str.contains(r" to ")]

    if len(debits) == 0:
        return "no top recipient account found"

    debits["names"] = debits["description"].apply(get_account_name, args=([" to "],))

    top_names = debits["names"].mode().to_list()

    if len(top_names) == len(debits):
        return "no top recipient account found"

    if len(top_names) == 1:
        return top_names[0]
    elif len(top_names) == 0:
        return "no top recipient account found"

    top_debits = debits.loc[debits["names"].isin(top_names)].groupby("names").sum()

    top_account_name = top_debits[
        top_debits["amount"] == top_debits["amount"].max()
    ].index[0]

    return top_account_name


def get_top_transfer_account(statement):
    credits = statement[statement["type"] == "C"]
    credits = credits[credits["description"].str.contains(r" from | frm ")]

    if len(credits) == 0:
        return "no top transfer account found"

    credits["names"] = credits["description"].apply(
        get_account_name, args=((" from ", " frm "),)
    )

    top_names = credits["names"].mode().to_list()

    if len(top_names) == len(credits):
        return "no top transfer account found"

    if len(top_names) == 1:
        return top_names[0]
    elif len(top_names) == 0:
        return "no top transfer account found"

    top_credits = credits.loc[credits["names"].isin(top_names)].groupby("names").sum()

    top_account_name = top_credits[
        top_credits["amount"] == top_credits["amount"].max()
    ].index[0]

    return top_account_name


def identify_loans(statement, keywords):
    loan_keywords = keywords[keywords["category"] == "loan"]["keyword"].to_list()
    loan_transactions = statement[
        statement["description"].str.contains("|".join(loan_keywords))
    ]

    loan_payments = round(
        float(loan_transactions[loan_transactions["type"] == "C"]["amount"].sum()), 2
    )

    unique_months = statement['date'].dt.strftime("%m/%y").nunique()
    
    repayment_transactions = loan_transactions[loan_transactions["type"] == "D"]
    loan_repayments = float(repayment_transactions["amount"].sum()) / unique_months
    loan_repayments = round(loan_repayments, 2)

    return loan_payments, loan_repayments
