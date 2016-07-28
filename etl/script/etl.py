# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os

from ddf_utils.str import to_concept_id, fix_time_range
from ddf_utils.index import create_index_file


# configuration of file paths
source = '../source/UNPD_WCU2015_Unmet_need_Country Data Survey-Based.xlsx'
out_dir = '../../'


def _fix_column_names(data):
    """There are 2 columns contains the column names.
    This function combine those columns and change the columns of dataframe.
    """
    for i in range(len(data.columns)):

        if not data.ix[0].isnull().ix[i]:
            name = data.iloc[0, i]

        else:
            name = ''

        if name:
            data = data.rename(columns={data.columns[i]: name})

    return data.drop([0])


def extract_entities_age(data):
    age = data[['Age']].copy()
    age['age'] = age['Age'].map(to_concept_id)
    age.columns = ['name', 'age']
    age = age.drop_duplicates()

    return age


def extract_entities_iso_code(data):
    country = data[['Country', 'ISO Code']]
    country = country.drop_duplicates().copy()
    country.columns = ['name', 'iso_code']
    country.iso_code = country.iso_code.map(int)

    return country


def extract_entities_unmet_need():
    unmet_need = pd.DataFrame([['limiting', 'Unmet need Limiting'],
                               ['spacing', 'Unmet need Spacing']],
                              columns=['unmet_need_section', 'name'])
    return unmet_need


def extract_concepts():
    """manually create the concept dataframe"""
    cdf = pd.DataFrame([['name', 'Name', 'string'],
                        ['iso_code', 'ISO Code', 'entity_domain'],
                        ['year', 'Year(s)', 'time'],
                        ['age', 'Age', 'entity_domain'],
                        ['unmet_need_section', 'Unmet need sections', 'entity_domain'],
                        ['unmet_need', 'Unmet need', 'measure']
                        ], columns=['concept', 'name', 'concept_type'])
    return cdf


def extract_datapoints(data):
    dps = data[['ISO Code', 'Year(s)', 'Age', 'Total', 'Spacing', 'Limiting']].copy()
    dps.columns = ['iso_code', 'year', 'age', 'total', 'spacing', 'limiting']

    dps.iso_code = dps.iso_code.map(int)
    dps.age = dps.age.map(to_concept_id)

    dps.year = dps.year.map(lambda x: fix_time_range(str(x)))
    dps = dps.set_index(['iso_code', 'year', 'age'])

    # total can be calculated with spacing and limiting. We will just save 2 sectors
    # in this dataset.
    sections = dps[['spacing', 'limiting']].copy()
    sections = sections.stack().reset_index()

    sections.columns = ['iso_code', 'year', 'age', 'unmet_need_section', 'unmet_need']

    return sections.sort_values(by=['iso_code', 'year', 'age'])


if __name__ == '__main__':
    data = pd.read_excel(source, na_values='..', skiprows=3)
    data = _fix_column_names(data)
    data = data.iloc[:, :8]

    print('creating concept files...')
    cdf = extract_concepts()
    path = os.path.join(out_dir, 'ddf--concepts.csv')
    cdf.to_csv(path, index=False)

    print('creating entities files...')
    # ages
    age = extract_entities_age(data)
    path = os.path.join(out_dir, 'ddf--entities--age.csv')
    age.to_csv(path, index=False)

    # iso_code
    iso_code = extract_entities_iso_code(data)
    path = os.path.join(out_dir, 'ddf--entities--iso_code.csv')
    iso_code.to_csv(path, index=False)

    # umnet_need_section
    unmet_need = extract_entities_unmet_need()
    path = os.path.join(out_dir, 'ddf--entities--unmet_need_section.csv')
    unmet_need.to_csv(path, index=False)

    print('creating datapoint files...')
    dps = extract_datapoints(data)
    path = os.path.join(out_dir,
                        'ddf--datapoints--unmet_need--by--iso_code--age--unmet_need_section--year.csv')
    dps.to_csv(path, index=False)

    print('creating index file...')
    create_index_file(out_dir)

    print('Done.')



