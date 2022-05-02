# Probably-the-best-Analysis-of-Business-Case-Netflix---Data-Exploration-and-Visualisation

Jupyter Notebook Link

https://colab.research.google.com/drive/19hGTsgYDCfGKHpnptDN-CyeqODjcggP7?usp=sharing


Problem Statement

Analyzing the information we have of the TV Show/Movie, it's cast, directors, release country, intended audience rating ,genre, release date and date when it's added to Netflix etc. to identify the characteristics/ingredients which make the Content(TV Show/Movie) popular and utilizing these insights to come up with recommendations for future content(genre, cast and director), the best time to launch the content and points of concern that need to be taken care of.

Basic Metrics which are used in the Analysis


1) Relationship between actors and number of Movies/TV Shows
2) Relationship between director and number of Movies/TV Shows
3) Relationship between country and number of Movies/TV Shows
4) Relationship between genre and number of Movies/TV Shows
5) Relationship between actor-director combination and number of Movies/TV Shows
6) Relationship between duration and number of Movies/TV Shows
7) Relationship between rating and number of Movies/TV Shows
8) Relationship between year of addition of content on Netflix and number of Movies/TV Shows
9) Relationship between month of addition of content on Netflix and number of Movies/TV Shows
10) Relationship between week of addition of content on Netflix and number of Movies/TV Shows
11) Relationship between actual year of release of Movies/TV Shows and number of Movies/TV Shows


Preliminary observation of our data

1) The datatype of all columns except release year is object while that of release year is int
2) The data has 8807 rows.
3) The director column has 2634 null values, cast has 825 null values,  country has 831 null values, 
date added has 10 null values, rating has 4 and duration has 3 null values.
4)The unique values and value counts have been incorporated in the Jupyter notebook attached here.

Data Preprocessing and Missing Value Imputation Approach 

1) In our data, 4 of our columns:- cast, director, country and listed_in have nested values which need to be unnested,
i.e- each row should have only one of the observations. 

2) As an initial step, 4 different dataframes each having title and the unnested version of nested columns are created
and joined. This joined data was later merged with the original data to get the remaining columns.  In the same step,
missing values of cast is imputed with Unknown Actor and missing values of director is imputed with Unknown Director.

3)duration column had 3 null values. As it turns out, those values weren't null but were mis written in ratings columns,i.e- ratings can't have the units as min. So the missing values of duration column were imputed with the 
corresponding values in ratings column. Those values in rating column were then replaced by 'NR',i.e- Non-Rated.

4)Imputation of missing values of Ratings was done with 'NR'.

5)date added column is imputed on the basis of release year,i.e- suppose 
there's a null for date_added when release year was 2013.So the written
code just checks the mode of date added for release year=2013
and imputes in place of nulls the corresponding mode.

6) For country column, imputation is done as follows:-
   a) checks for directors of countries with missing data and look for non-null
      entries of the country column for same director and imputes by mode of the 
      country of the director.
   
   b) There would definitely be entries having directors with only one occurence
      and countries with null values. So for them, I have used the modal country of
      the Actor in non-null entries.

   c) There would still be few countries left and they are imputed with Unknown Country.

7)Duration of movies is given in minutes and that of TV Shows in Seasons in our data.
For our convenience I have binned the duration of movies in mins(created 7 bins) based
on observation of distribution of duration of movies.

8)Extracted month and week number from the date added column of our data.

9)Titles such as Bahubali(Hindi Version),Bahubali(Tamil Version) were there.
 Since it's only one movie in different languages,
 presence of brackets and content between brackets is removed.     

Levels of Analysis

Analysis has been done in 3 levels:-
a) In Level 1, the whole content of Netflix is taken into account as one,
i.e- no distinction between TV Shows and Movies during the analysis 
on the basis of metrics depicted above.

b)In Level 2, separate analysis has been done for TV Shows and Movies 
on the basis of metrics depicted above.

c)In Level 3, an insight had been taken from Levels1 and 2 regarding the 
countries for TV Shows and Movies. USA, India and UK have been analyzed for 
both TV Shows and Movies while Japan and South Korea have been analyzed for 
TV Shows. These countries have been chosen on the basis of number of popular titles.


Level 3 was intended to come up with detailed granular insights and recommendations.


Insights from Level 1 Analysis:-

1)  We have almost  70:30 ratio of Movies and TV Shows in our data.

2) US,India,UK,Canada and France are leading countries in Content Creation on Netflix.

3)Most of the highly rated content on Netflix is intended for Mature Audiences, R Rated, content not intended for audience under 14 and those which require Parental Guidance.

4) The duration of Most Watched content in our whole data is 80-100 mins.

5) Anupam Kher,SRK,Julie Tejwani, Naseeruddin Shah and Takahiro Sakurai 
occupy the top stop in Most Watched content.

6) Rajiv Chilaka, Jan Suter and Raul Campos are the most popular 
directors across Netflix

7)The Amount of Content across Netflix has increased from 2008 continuously till 2019. 
Then started decreasing from here(probably due to Covid)

8)Most of the content is added in the first and last months across Netflix.

9)Net content release which are later uploaded to Netflix has increased since 1980
 till 2020 though later reduced certainly due to COVID-19

Insights from Level 2 Analysis:-

1) International TV Shows, Dramas and Comedy Genres are popular across TV Shows 
  in Netflix. International Movies, Dramas and Comedy Genres are popular 
   followed by Documentaries across Movies on Netflix.

2)United States is leading across both TV Shows and Movies, 
UK also provides great content across TV Shows and Movies. 
India is much more prevalent in Movies as compared TV Shows. 
Moreover the number of Movies created in India outweigh the sum 
of TV Shows and Movies across UK since India was rated 
as second in net sum of whole content across Netflix.

3)The popular ratings across Netflix includes Mature Audiences and those 
appropriate for over 14/over 17 ages.

4) Across TV Shows, shows having only 1 Season are common as soon as 
the season length increases,
the number of shows decrease and this definitely sounds as expected.
Across movies 80-100,100-120 and 120-150 is the ranges of minutes for which most 
movies lie. So quite possibly 80-150 mins is the sweet spot 
we would be wanting for movies.
  
5) Takahiro Sakurai,Yuki Kaji and other South Korean/Japanese 
actors are the most popular actors across TV Shows indicating 
that TV Shows in Japan and South Korea need a separate analysis.
Our bollywood actors such as Anupam Kher, SRK, Naseeruddin Shah 
are very much popular across all movies on Netflix.

7) Ken Burns, Alastair Fothergill, Stan Lathan, Joe Barlinger are 
popular directors across TV Shows on Netflix.
Rajiv Chilka, Jan Suter, Raul Campos, Suhas Kadav are popular directors
across movies on Netflix. 

8)Till 2019, overall content across Netflix was increasing
 but due to Covid in 2020, though TV Shows didn't take a hit then Movies 
did take a hit. Well later in 2021, content across both was reduced significantly.


9)TV Shows are added in Netflix by a tremendous amount in mid weeks/months 
of the year, i.e- July
Movies are added in Netflix by a tremendous amount in first week/
last month of current year and first month of next year.





Insights from Level 3 Analysis:-

Part A) Insights for Netflix Content in USA

1) Dramas,Comedy, Kids 'TV Shows, International TV Shows 
and Docuseries, Genres are popular in TV Series in USA.
Dramas,Comedy, Documentaries, Family Movies and Action 
Genres in Movies are popular in USA

2) The popular ratings
 across Netflix includes Mature Audiences and those appropriate
 for over 14/over 17 ages in both Movies and TV Shows in USA

3) Across movies 80-100,100-120 is the ranges of minutes for which most movies lie.
 So quite possibly 80-120 mins is the sweet spot we would be wanting 
 for movies in USA

4)Vincent Tong,Grey Griffin and Kevin Richardson are the most 
popular actors across TV Shows in USA.
Samuel Jackson,Adam Sandler,James Franco and Nicolas Cage are very 
much popular across movies on Netflix in USA


5)Ken Burns,Stan Lathan, Joe Barlinger are popular directors across 
TV Shows on Netflix in USA
Jay Karas,Marcus Raboy,Martin Scorcese and Jay Chapman are 
popular directors across movies in USA

6)In USA, number of shows remained the same in 2021 as they 
were in 2020 while number of movies declined.

7)TV Shows are added in Netflix by a tremendous amount in July 
and September in USA.
Movies are added in Netflix in USA by a tremendous amount in first 
week/last month of current year and first month of next year

8)In USA, though New Releases of both Movies and Shows have reduced in 2021, 
the amount of decrease in number of TV Shows is small as compared to Movies.


9)The Most Popular Actor Director Combination in Movies Across USA are:-
'Smith Foreman and Stanley Moore',
'Marlon Wayans and Michael Tiddes',
'Adam Sandler and Steve Brill',
'Maisie Benson and Stanley Moore',
'Ashleigh Ball and Ishi Rudell',
'Tara Strong and Ishi Rudell',
'Rebecca Shoichet and Ishi Rudell',
'Kerry Gudjohnsen and Alex Woo',
'Kerry Gudjohnsen and Stanley Moore',
'Paul Killam and Alex Woo',
'Paul Killam and Stanley Moore',
'Andrea Libman and Ishi Rudell',
'Kevin Hart and Leslie Small',
'Maisie Benson and Alex Woo',
'Alexa PenaVega and Robert Rodriguez',
'Tabitha St. Germain and Ishi Rudell'

The Second Most Popular Actor Director Combination in Movies Across USA are:-
'Rory Markham and Mike Gunther',
'Erin Mathews and Steve Ball',
'Danny Trejo and Robert Rodriguez',
'Jeff Dunham and Michael Simon'



Part B) Insights for Netflix Content in India

1) Dramas,Comedy, Kids 'TV Shows and International TV Shows 
Genres are popular in TV Series in India.
International Movies,Drama,Comedy,Indpeendent Movies and Action, 
Romance Genres are prevalent in India.

2)So it seems plausible to conclude that the popular ratings across Netflix 
includes Mature Audiences in TV Shows and those appropriate for people over
14 in Movies in India.
Now this indeed seems to be the case. Popular Indian TV Shows in Netflix are 
without a shadow of doubt intended for Mature Audiences while Movies for 
over 14 years of age.


3)Across movies ranges of minutes in India are comparatively 
greater than USA with a sweet spot at 120-150 mins.

4)Popular Actors in TV Shows in India are:-
'Rajesh Kava',
'Nishka Raheja',
'Prakash Raj',
'Sabina Malik',
'Anjali',
'Aranya Kaur',
'Sonal Kaushal',
'Chandan Anand',
'Danish Husain'

Popular actors across Movies in India:-
'Anupam Kher',
'Shah Rukh Khan',
'Naseeruddin Shah',
'Akshay Kumar',
'Om Puri',
'Paresh Rawal',
'Julie Tejwani',
'Amitabh Bachchan',
'Boman Irani',
'Rupa Bhimani',
'Kareena Kapoor',
'Ajay Devgn',
'Rajesh Kava',
'Kay Kay Menon'


5)Popular Directors Across TV Shows in India:-
'Gautham Vasudev Menon',
'Abhishek Chaubey',
'Sudha Kongara',
'Rathindran R Prasad',
'Sankalp Reddy',
'Sarjun',
'Soumendra Padhi',
'Srijit Mukherji',
'Tharun Bhascker Dhaassyam'

Popular directors across movies in India:-
'Rajiv Chilaka',
'Suhas Kadav',
'David Dhawan',
'Umesh Mehra',
'Anurag Kashyap',
'Ram Gopal Varma',
'Dibakar Banerjee',
'Zoya Akhtar',
'Tilak Shetty',
'Rajkumar Santoshi',
'Priyadarshan',
'Sooraj R. Barjatya',
'Ashutosh Gowariker',
'Milan Luthria'


6)In India,TV Shows were increasingly being added till 2020, 
though the addition of shows reduced in 2021.
In India, Movies were increasingly added till 2018 but it has 
been a huge downhill since then. Now that's preposterous,
since and soemthing has to be recommended to the Netflix Team 
with regards to that.

7)TV Shows are added in Netflix by a tremendous amount in April in India
Movies are added in Netflix in India by a tremendous amount in 
first week/last month of current year and first month of next year

8)The understandable trend amongst movies and TV Shows across India 
in Netflix is the reduction of movies after 2020

9)The Most Popular Actor Director Combination in Movies Across India are:-
'Rajesh Kava and Rajiv Chilaka',
'Julie Tejwani and Rajiv Chilaka',
'Rupa Bhimani and Rajiv Chilaka',
'Jigna Bhardwaj and Rajiv Chilaka',
'Vatsal Dubey and Rajiv Chilaka',
'Mousam and Rajiv Chilaka',
'Swapnil and Rajiv Chilaka',
'Saurav Chakraborty and Suhas Kadav',
'Smita Malhotra and Tilak Shetty',
'Anupam Kher and David Dhawan',
'Salman Khan and Sooraj R. Barjatya',



Part C) Insights for Netflix Content in UK

1) British TV Shows,International TV Shows,Docuseries, 
Crime, Comedy are widely watched Genres in TV Shows in UK.
International Movies,Drama,Comedy,Indpeendent Movies and Action, 
Romance Genres in Movies are prevalent in UK.

2)It seems plausible to conclude that the popular ratings 
across Netflix includes Parental Guidance and Mature Audiences in 
TV Shows and R Rated+MA Rated in Movies in UK

3)Across movies ranges of minutes in UK have a sweet spot at 80-120 mins.

4)Popular Actors in TV Shows in UK are:-
'David Attenborough',
'Terry Jones',
'Graham Chapman',
'John Cleese',
'Eric Idle',
'Michael Palin',
'Terry Gilliam',
'Teresa Gallagher',
'Harriet Walter'

Popular actors across Movies in UK:-
'John Cleese',
'Michael Palin',
'Judi Dench',
'Keith Wickham',
'Eric Idle',
'Brendan Gleeson',
'Terry Gilliam',
'Terry Jones',
'Helena Bonham Carter',
'Graham Chapman',
'Samuel West',
'Eddie Marsan',
'James Cosmo',
'Rob Rackstraw'


5)Popular directors across movies in UK:-
'Joey So',
'Edward Cotterill'

6)In terms of TV Shows, UK saw a downfall in 2018 from 2017, 
then a great increase in 2019 but has been reducing since then.
In terms of Movies,the number of popular movies in UK increased 
till 2019, since then it's decreasing.

7)TV Shows are added in Netflix by a tremendous amount in March in UK
Movies are added in Netflix in India by a tremendous amount in first week/
last month of current year and first month of next year

8)Same trend of reduction in newly released movies and shows after 2020.


9) The Most Popular Actor Director Combination in Movies Across UK are:-
'Keith Wickham and Joey So',
'Rob Rackstraw and Joey So'





Part D) Insights for Netflix TV Shows in Japan

1)International TV Shows and Anime Genres are popular in TV Shows in Japan

2)It seems plausible to conclude that the popular ratings across 
Netflix includes TV-14 Mature Audiences in TV Shows 

3)Popular Actors in TV Shows in Japan are:-
'Takahiro Sakurai',
'Yuki Kaji',
'Daisuke Ono',
'Junichi Suwabe',
'Ai Kayano',
'Yuichi Nakamura',
'Yoshimasa Hosoya',
'Jun Fukuyama',
'Hiroshi Kamiya',
'Kana Hanazawa'

4)In Japan, TV Shows have diminished in 2017 from 2016 and then 
increased till 2020 after which it has reduced in 2021.

5)TV Shows are added in Netflix by significant numbers in April and January in Japan

6)Reduction in Newly Released TV Shows after 2019 in Japan


Part E) Insights for Netflix TV Shows in South Korea

1) International TV Shows,Romantic TV Shows,Drama,
Crime and Comedy Genres are popular in TV Shows in S.Korea.

Only S.Korea has Romance as a top 3 favorable genre 
which depicts an inclination of their audience.

2)It seems plausible to conclude that the popular ratings 
across Netflix includes TV-14 and Mature Audiences in TV Shows 

3)Popular Actors in TV Shows in South Korea are:-
'Sung Dong-il',
'Kim Won-hae',
'Cho Seong-ha',
'Nam Joo-hyuk'

4)In South Korea, number of TV Shows reduced in 2018 from 2017, 
then increased till 2019 but have been on a heavy downfall since then.

5)TV Shows are added in Netflix by significant numbers in May and January in South Korea

6) The number of newly released TV Shows in S.Korea reached peak in 2016. It then reached  
a second peak in 2019. It has reduced in 2021 from 2020.





Recommendations

1) The most popular Genres across the countries and in both TV Shows and Movies are 
Drama, Comedy and International TV Shows/Movies, so content aligning to that 
is recommended.

2)Add TV Shows in July/August and Movies in last week of the year/first month of 
the next year.

3)For USA audience 80-120 mins is the recommended length for movies and Kids TV Shows
are also popular along with the genres in first point, hence recommended.

4)For UK audience, recommended length for movies is same as that of USA (80-120 mins)

5)The target audience in USA and India is recommended to be 14+ and above ratings while
for UK, its recommended to be completely Mature/R content .

6)Add movies for Indian Audience, it has been declining since 2018.

7)Anime Genre for Japan and Romantic Genre in TV Shows for
 South Korean audiences is recommended.

8) While creating content, take into consideration the popular actors/directors
for that country. Also take into account the director-actor combination which 
is highly recommended. 
