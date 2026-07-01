# IAT Protocol Documentation

## Dataset Source
**Source**: Project Implicit Data Archive
**Dataset Name**: Political IAT (Standard Protocol)
**Access**: (Public/Restricted Archive)
**Data Collection Period**: 2000–Present (Archived)

## Stimulus Set Details
This analysis utilizes the standard "Political IAT" protocol developed by Project Implicit.
The protocol measures the strength of automatic associations between mental concepts.
The specific stimulus set is fixed and static, satisfying Constitution Principle VI for reproducible offline analysis.

### Target Categories (Concepts)
The target concepts distinguish between political affiliations:
- **Liberal**: Associated with the category label "Liberal".
- **Conservative**: Associated with the category label "Conservative".

### Attribute Categories (Valence)
The attribute concepts distinguish between evaluative valence:
- **Good**: Associated with positive affect.
- **Bad**: Associated with negative affect.

### Stimulus List
The following word lists constitute the standard stimulus set used in the Project Implicit Political IAT.
These words are presented visually during the task blocks.

| Category | Stimuli (Words) |
|:--- |:--- |
| **Liberal** | Democrat, Liberal, Progressive, Left, Democratic, Freedom, Openness, Tolerance |
| **Conservative** | Republican, Conservative, Right, Traditional, GOP, Order, Tradition, Stability |
| **Good** | Joy, Love, Peace, Wonderful, Pleasant, Friend, Happy, Excellent, Success, Angel |
| **Bad** | Agony, Terrible, Horrible, Nasty, Evil, War, Failure, Disaster, Hurt, Enemy |

*Note: The exact ordering of words is randomized per participant, but the pool of words remains constant for the standard protocol.*

## Software Version & Implementation
- **Platform**: Project Implicit Web-Based IAT (JavaScript/HTML5)
- **Version**: Standard v2.0 (Current Archive Standard)
- **Algorithm**: D-Score Algorithm (Greenwald, Nosek, & Banaji, 2003)
- **Data Format**: CSV (Response Latencies, Block IDs, Stimulus Codes)

## Constitution Principle VI Compliance
This documentation confirms that the analysis relies on a static, well-defined stimulus set from the Project Implicit archive.
The D-score algorithm is applied to the response latencies recorded in the dataset.
No live interaction with the external web service is required during the analysis phase, ensuring the study is reproducible via static data analysis.

## References
1. Greenwald, A. G., McGhee, D. E., & Schwartz, J. L. (1998). Measuring individual differences in implicit cognition: the implicit association test. *Journal of Personality and Social Psychology*, 74(6), 1464–1480.
2. Nosek, B. A., Greenwald, A. G., & Banaji, M. R. (2005). Understanding and using the Implicit Association Test: II. Method variables and construct validity. *Personality and Social Psychology Bulletin*, 31(2), 166–180.
3. Project Implicit. (2023). *Project Implicit Data Archive*. Retrieved from 