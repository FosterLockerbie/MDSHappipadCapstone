import pandas as pd
import ast

def convert_string_list_columns(df, columns_to_convert):
    """
    Converts string representations of lists in the specified columns of a DataFrame
    to actual Python lists.

    Args:
        df (pd.DataFrame): The DataFrame to process.
        columns_to_convert (list): A list of column names to convert.

    Returns:
        pd.DataFrame: The processed DataFrame.
    """
    for col in columns_to_convert:
        if col in df.columns:
            def safe_eval(string_list):
                """Safely evaluates a string, returning a list or None."""
                if isinstance(string_list, str):
                    try:
                        # Attempt to use ast.literal_eval
                        return ast.literal_eval(string_list)
                    except (ValueError, SyntaxError):
                        # If not a valid literal, attempt string splitting
                        cleaned_string = string_list.strip("'")
                        items = [item.strip().strip("'") for item in cleaned_string.split(', ')]
                        return items
                elif isinstance(string_list, list):
                    return string_list  # If already a list, no conversion needed
                return None  # Return None for other types

            df[col] = df[col].apply(safe_eval)
        else:
            print(f"Column '{col}' not found in DataFrame.")
    return df

def load_data():
    # Load raw CSVs
    properties = pd.read_csv('../data/properties_clean_list.csv')
    contracts = pd.read_csv('../data/contracts.csv')
    df = pd.read_csv('../data/cleaned_renters.csv', parse_dates=['Registered At'])
    city_df = pd.read_csv('../data/city_df.csv')

    # Merge city info
    df = df.merge(city_df, how='left', left_on='City_extracted', right_on='City')

    # Convert date columns and extract year
    properties['Date'] = pd.to_datetime(properties['Available From'])
    properties['Year'] = properties['Date'].dt.year
    contracts['Date'] = pd.to_datetime(contracts['Signed Date'])

    # Process list-like string columns in properties
    columns_to_process = ['Furnishings', 'Safety Features', 'Amenities', 'House Rules']
    properties = convert_string_list_columns(properties, columns_to_process)

    return properties, contracts, df, city_df
