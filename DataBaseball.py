import pandas as pd
from unidecode import unidecode

# Show all columns when displaying player stats.
# Source: https://stackoverflow.com/questions/11707586/how-do-i-expand-the-output-display-to-see-more-columns-of-a-pandas-dataframe
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 800)

# Master file that has the player's name corresponding to their playerID.
people_file = 'C:\\Users\\Brian Bui\\OneDrive\\Desktop\\361\\A4\\baseballdatabank-2023.1\\core\\People.csv'

# Pertinent files
batting_file = 'C:\\Users\\Brian Bui\\OneDrive\\Desktop\\361\\A4\\baseballdatabank-2023.1\\core\\Batting.csv'
fielding_file = 'C:\\Users\\Brian Bui\\OneDrive\\Desktop\\361\\A4\\baseballdatabank-2023.1\\core\\Fielding.csv'
pitching_file = 'C:\\Users\\Brian Bui\\OneDrive\\Desktop\\361\\A4\\baseballdatabank-2023.1\\core\\Pitching.csv'

# Reads the csv files into the form of a data frame.
people_df = pd.read_csv(people_file)
batting_df = pd.read_csv(batting_file)
fielding_df = pd.read_csv(fielding_file)
pitching_df = pd.read_csv(pitching_file)


# Removes accents from strings.
# Source: https://www.geeksforgeeks.org/how-to-remove-string-accents-using-python-3/
def normalize_string(text):
    if pd.isna(text):  # Return an empty string for NaN values
        return ""
    return unidecode(text)


def find(input_name):
    normalized_name = normalize_string(input_name).lower()
    names = normalized_name.split()  # Creates a list from the name to search for nameFirst and nameLast

    # If the input has only 1 string, it can either be a first or last name.
    if len(names) == 1:
        name = names[0]
        mask = people_df['nameFirst'].str.lower().str.contains(name.lower(), na=False) | \
               people_df['nameLast'].str.lower().str.contains(name.lower(), na=False)

    # If the input has 2 strings, then the input was a first name then last name.
    else:
        first_name, last_name = names[0], ' '.join(names[1:])
        mask = people_df['nameFirst'].str.lower().str.contains(first_name.lower(), na=False) & \
               people_df['nameLast'].str.lower().str.contains(last_name.lower(), na=False)

    potential_matches = people_df[mask]  # Determines if there are or are not potentially matching names.

    # If there are potential matches
    if not potential_matches.empty:
        # If there is an exact match or only 1 player fits the criteria.
        if len(potential_matches) == 1:
            first_name, last_name = potential_matches.iloc[0]['nameFirst'], potential_matches.iloc[0]['nameLast']
            print(f"\nDisplaying stats for {first_name} {last_name}:")
            search_and_display_player_stats(first_name, last_name)

        # If there are multiple players the user could be referring to.
        else:
            print(f"\nThere are multiple players with '{input_name}' in their full name.\n"
                  f"Here is a full list of potential matches:\n")
            print(potential_matches[['nameFirst', 'nameLast']].to_string(index=False))
            print()

    # There are no potential matches.
    else:
        print(f"\nDataBaseball was unable to find {input_name}.\n"
              f"Please try again or press 0 to return to the starting menu.\n")


# Uses the player's name to obtain a playerID that is used to search each category.
def search_and_display_player_stats(first_name, last_name):
    row = people_df[(people_df['nameFirst'].str.lower() == first_name.lower()) &
                    (people_df['nameLast'].str.lower() == last_name.lower())]

    if not row.empty:
        playerID = row.iloc[0]['playerID']
        display_player_stats(playerID)
    print()


def display_player_stats(playerID):
    # List of (category data frame, category title)
    categories = [
        (batting_df,
         "*********************************************"
         " BATTING STATS "
         "*********************************************"),
        (pitching_df,
         "**************************************************************"
         " PITCHING STATS "
         "**************************************************************"),
        (fielding_df,
         "**********************************"
         " FIELDING STATS "
         "**********************************"),
    ]

    # Combs each category looking for a matching playerID to display the given row.
    for df, category_header in categories:
        player_records = df[df['playerID'] == playerID].iloc[:, 1:]
        if not player_records.empty:
            print(f"\n{category_header}")
            print(player_records.to_string(index=False))


# Starting menu that allows input.
while True:
    player_input = input("Enter the player's name (can be first, last, or both): ")
    if player_input == "0":
        break
    find(player_input)
