
# OpenStreetMap data wrangling project

## 1. City of data
___

**Name:** Dubai  <br />
**URL :**  https://www.openstreetmap.org/relation/4479752#map=9/25.0769/55.4576 <br />
**OSM data url:** https://mapzen.com/data/metro-extracts/metro/dubai_abu-dhabi/

Dubai is a beautiful city and I always want to visit there, so I choose its dataset and I am curious about what I will found from it. Another reason is that Dubai's data is the most popular dataset on OpenStreetMap, and the size of data is large enough for this project.

## 2. Problems I met in data wrangling
---

At first, I used the code in former lessons to audit the raw data by listting all 'k' and 'v' values, then I found there are two inconsistent problems in the raw osm data. One is **inconsistent key name problem**, it means different key names indicate the same attribute, for example: motorcar and motor_vehicle are all represent cars, but they are different names. Another problem is **inconsistent value format**, for instance, "+ 917 (0) 4 359 8888" and "+ 917 2 445-90-19" are both phone numbers with distinct format. Then I will show more details in the following.

**I used following code to audit and correct inconsistent keys and values:**


```python
#audit and correct inconsistent keys and values.
def audit_element(elem):
    if elem.tag == 'node':
        for k in elem:
            #better_key function use to audit and correct key's name
            k.attrib['k'] = better_key(k.attrib['k'])
            #better_value function use to audit and unify value's format
            k.attrib['v'] = better_value(k.attrib['k'], k.attrib['v'])
    elif  elem.tag == 'way':
        for k in elem:
            if k.attrib.has_key('k'):
                k.attrib['k'] = better_key(k.attrib['k'])
                k.attrib['v'] = better_value(k.attrib['k'], k.attrib['v'])
    return elem
```

## 2.1 Inconsistent key name problem:

By outputting all the keys in 'node' and 'way' tags, I found several inconsistent key name, for example **'phone'** and **'phone_1'**; **'motorcar'** and **'motor_vehicle'**; **'old_name'**, **'old_name_1'** and **'old_name_2'**. In each group, the key names represent the same attributs, in order to query them in the future, I made those key names consistnet. For example:


```python
#In my audit outbput, there are:
'motor_vehicle': 40     #There are 40 keys named motor_vehicle
'motorcar': 27          #There are 27 keys named motorcar
```

**I used better_key function to audit and correct key names.**


```python
key_mapping = {"motorcar": "motor_vehicle",
               "old_name_1": "old_name",
               "old_name_2": "old_name",
               "phone_1":" phone"
}

# Unify key' format
def better_key(key):
    if key_mapping.has_key(key):
        return key_mapping[key]
    else:
        return key
```

## 2.2 Inconsistent value format problem 

In the raw data, I also found that the same attribute's values have different format. So another problem I have to solve is unifying them into the same format. I corrected the format of phone number, city name, and street format. I will discuss them int he following content.

**I used better_value function to audit and correct value format**


```python
# Unify value format
def better_value(key, value):
    if key == "addr:street":
        value = update_street_name(value, street_mapping)
        return value
    elif key == "addr:city":
        value = update_city_name(value)
        return value
    elif key == "phone":
        value = update_phone_name(value, phone_bad_char)
        return value
    else:
        return value
```

## 2.2.1 Correct Phone number format

Wrong format example:<br\>
    **'+ 971 (0) 4 259 8888'** VS **'+971 2 445-90-19'**


```python
#Bad characters in phone numbers
phone_bad_char = [" ", "+", "-", "(", ")"]

# correct phone number format
def update_phone_name(number, phone_bad_char):
    for bc in phone_bad_char:
        if bc in number:
            number = number.replace(bc, "")
            return number
```

The way I unify phone number format is removing bad characters( in array phone_bad_char ) from the number. After that most of phone numbers had the same format. For example:

![phone_audit.png](attachment:phone_audit.png)

## 2.2.2 Correct street format

Wrong format example:<br\>
    **'12 D St' VS '12 D Street'**


```python
# street mapping array
street_mapping = {"St": "Street",
                  "St.": "Street",
                  "Ave": "Avenue",
                  "Rd.": "Road",
                  "road": "Road"
                 }

# correct street format
def update_street_name(street_name, street_mapping):
    result = street_name
    if "Steet" in street_name:
        result = street_name.replace("Steet", "Street")
        return result
    else:
        for c in street_mapping:
            if c in street_name and street_mapping[c] not in street_name:
                result = street_name.replace(c, street_mapping[c])
                break # not jump out of if statement, but jump out of the whole for loop
                return result
```

I solved this problem by replacing abbreviations (eg: St) by thir full denote (eg: St => Street). After that most of street had the same format. For example:

![Screen%20Shot%202017-08-31%20at%2023.19.57.png](attachment:Screen%20Shot%202017-08-31%20at%2023.19.57.png)

## 3. Overview of the data

## 3.1 File size

**dubai_abu-dhabi.osm: -------------- 527.5 Mb ** <br/>
**osm.db: --------------------------- 267   Mb ** <br/>
**nodes.csv: ------------------------ 199.8 Mb ** <br/>
**nodes_tags.csv: ------------------- 11.7  Mb ** <br/>
**ways.csv: ------------------------- 19.4  Mb ** <br/>
**ways_nodes.csv: ------------------- 70.2  Mb ** <br/>
**ways_tags.csv: -------------------- 26    Mb ** <br/>

## 3.2 Overview statistics of the dataset 

## number of unique users

```sql
select count(distinct(uid)) from nodes
UNION
select count(distinct(uid)) from ways;
```

**Ans: 2453**

## number of nodes

```sql
select count(uid) from nodes;
```

**Ans: 2431532**

## number of ways

```sql
select count(uid) from nodes;
```

**Ans: 324346**

## number of toilets

```sql
select count(*) from nodes_tags where key = 'toilets'
UNION All
select count(*) from ways_tags  where key = 'toilets';
```

**Ans: 6** <br\>
This answer is wierd, because I can't believe there are just 6 toilets in Dubai.

## number of distinct key

```sql
select count(distinct(both.key))
from (select * from nodes_tags
        union all
      select * from ways_tags) as both
```

**Ans: 860**

## Top 10 popular key

```sql
select both.key, count(both.key)
from (select key from nodes_tags
        union all
      select key from ways_tags) as both
group by both.key
order by count(both.key)
desc
limit 10;
```

**ANS:** <br\>
highway,185955<br\>
source,92113<br\>
building,89917<br\>
name,78347<br\>
surface,75416<br\>
oneway,70296<br\>
street,53102<br\>
lanes,38043<br\>
ar,31977<br\>
housenumber,30096<br\>

## 4. Other ideas about the dataset

### Cross-validating incorrect or missing data from Google map or rewarding manually corrections

There are a lot of incorrect or missing values in original data, possibly due to randomly editing without any validation.For example:
* Total number of palces: 444151
* Number of Places have phone number: 907
* Percentage of places have phone number: 0.2%
Acooirding to the statistic above, I found most of nodes has no phone number information, but phone numbers are important for most places. Fortunately, we can use Google Map API to add phone numbers, office hours or other critical information. And we can also improve openstreetmap data by rewarding people who make correct data or modification. Those solutions can produce higher quality data than before and expend community of openstreetmap. Another benefit Google Map API can offer is Google API let us search by language parameter, its good to search by different language, like Dubai use Arabic.

However there still some problems of the improvment above. First, Google Map API need particular key which is not convenient sometimes. Second, Google map can not cover all the places, although we can solve it by adding other map API, but it will using other APIs and more difficult to use and maintain.

## Additional Queries

## Total number of places

```sql
select count(DISTINCT(both.id))
from (select * from nodes_tags
        union all
      select * from ways_tags) as both
```

**Ans: 444151**

## Places have phone number

```sql
select count(distinct(both.id))
from (select * from nodes_tags
          union all
        select * from ways_tags) as both
where both.key = 'phone';
```

**ANS: 907**

## Conclusion

This is a interesting and helpful project. By finishing this project, I goes through the whole data wrangling procee and got a deeper understanding about data wrangling. I still need to practice more about data auditing and cleaning, because there are still a lot of incorrectness in Dubai's data but I don't know what to do with them, for example some phone number is not start with 917 and shorter than others. And I believe this data just decribe part of Dubai, because I can not believe there are only 6 toilets in Dubai. What's more there are some problems in the data and I think we can use google map api and other ways to solve the problem and improve the quality of data.

## Reference

[1] https://gist.github.com/carlward/54ec1c91b62a5f911c42#problems-encountered-in-the-map<br/>
[2] https://wiki.openstreetmap.org/wiki/Main_Page<br/>
[3] https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet#lists<br/>
[4] https://en.wikipedia.org/wiki/OpenStreetMap<br/>
[5] https://www.w3schools.com/sql/sql_like.asp<br/>


```python

```
