import pandas as pd
import os


def full_info(query):
    df = pd.read_csv(os.path.join(os.path.dirname(
        __file__), 'data', 'merge_cloth.csv'))
    selected_row = df[df['cloth_path'] == query]

    # Extract the desired information
    color = selected_row['color'].values[0]
    price = selected_row['price'].values[0]
    rates = selected_row['rates'].values[0]
    url = selected_row['url'].values[0]
    material = selected_row['material'].values[0]

    return (color, price, rates, url, material)
