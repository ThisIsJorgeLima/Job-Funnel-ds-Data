# QuickHire

You can find the project at [QuickHire.dev](https://quickhire.dev)

## Contributors

|[Pierre Nelson](https://github.com/alxanderpierre)                                                                                            |[Logan Keith](https://github.com/lrizika)                                                                                                    |[Baisal Ergeshev](https://github.com/Baisal89)|                                                                                                                                                                                                 
| :-----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: |
|                      [<img src="https://avatars0.githubusercontent.com/u/51343473?s=400&v=4" width = "200" />](https://github.com/alxanderpierre)                       |                      [<img src="https://ca.slack-edge.com/T4JUEB3ME-UMHPCN3NW-ab422991fa22-512" width = "200" />](https://github.com/lrizika)                       |                      [<img src="https://ca.slack-edge.com/T4JUEB3ME-UJRSD5X6H-c2998ebc2ac3-512" width = "200" />](https://github.com/Baisal89)                       |                      [<img src="https://www.dalesjewelers.com/wp-content/uploads/2018/10/placeholder-silhouette-female.png" width = "200" />](https://github.com/)                       |                      [<img src="https://www.dalesjewelers.com/wp-content/uploads/2018/10/placeholder-silhouette-male.png" width = "200" />](https://github.com/)                       |
|                 [<img src="https://github.com/favicon.ico" width="15"> ](https://github.com/alxanderpierre)                 |            [<img src="https://github.com/favicon.ico" width="15"> ](https://github.com/lrizika)             |           [<img src="https://github.com/favicon.ico" width="15"> ](https://github.com/Baisal89)            |                     |                        |
| [ <img src="https://static.licdn.com/sc/h/al2o9zrvru7aqj8e1x2rzsrca" width="15"> ](https://www.linkedin.com/in/pierre-nelson-26838a148/) | [ <img src="https://static.licdn.com/sc/h/al2o9zrvru7aqj8e1x2rzsrca" width="15"> ](https://www.linkedin.com/in/logan-k-3802b0195/) | [ <img src="https://static.licdn.com/sc/h/al2o9zrvru7aqj8e1x2rzsrca" width="15"> ](https://www.linkedin.com/in/baisal-ergeshev-52b3b342/) | 
<br>
<br>

## Project Overview

https://github.com/Lambda-School-Labs/Job-Funnel-ds-API/tree/master/docs


[Trello Board](https://trello.com/b/dorhqi4o/job-funnel)

[Product Canvas](https://www.notion.so/Job-Funnel-20ba287fac1c403c92a8ebb8766821a0)

[UX Design files](https://www.figma.com/file/zljtkyosMyzAa1UMpcAIEd/Quick-Hire-Judy?node-id=263%3A2)

[Backend Documentation](https://github.com/Lambda-School-Labs/Job-Funnel-be)

[Data Science Repo](https://github.com/Lambda-School-Labs/Job-Funnel-ds-API)

## Quickhire Description

Quickhire is a web application that streamlines the job search process by allowing users to search, store, and apply for jobs -- all in one place. It allows you, as a user, to login, search for jobs that you're interested in, save them, and apply to them. 

Our mission is to simplify the job-search and hiring process by bringing both to the same platform. Future releases will include a recruiter side of the app, which will allow for both kinds of users to interact with one another --- whether it be through initial contact, through an interview, or through any part of the job search process. 


### Tech Stack

List all of the languages, frameworks, services: Python, Selenium, PostgresSQL, AWS Elastic Beanstalk, AWS Lambda function, AWS RDS. 

## Project Overview

Finding jobs you like is hard. When you find many jobs you like, it’s hard to organize and prioritize them. It’s also hard to know your probability of getting a job based on it’s description.
Help students get the best jobs matched to them using data science. And give them an awesome interface to store and and manage the jobs they want to pursue.

### Dataset

We use the first 10,000 jobs listing that we scraped to train our model.

### Models

Created a topic model to discover the topics that occured in our collection of documents to filter them for the grad. The type of topic model that we use was a LDA model. we use the gensim lib. Here is a link to the documentation https://radimrehurek.com/gensim/auto_examples/tutorials/run_lda.html

# from gensim.utils import simple_preprocess

We first had to tokenize the sentences into a list of words.

# Bi-grams and Tri-grams

We then wanted to find the world that appeared the most times together. Such as Machine Learning/ Data Science etc.

# Lemmatization and STOPWORDS

We create a stopwords function to get rid of words that we thought we not useful and also implemented LEMMATIZATION to only allow for nouns adjs verbs and advs. This may be something that you may want to change later.

# Dictionary

Next we create a Dictionary and an id2word by importing import gensim.corpora as corpora. And also use a filter no_below to only allow words that appeared in at least 5 documents into our model. no_above for the purpose of making sure that to only include words that appeared in 90% of the corpus.

# LDA Model.

Once we created the model we then tuned the hyper parameters accordingly. However we checked to see how good our model was by using a Coherence Score.

# Coherence Score.

The best we got was a little above .60. The higher you go the more you will run into over fitting.
However in the notebook the large commented out protion is us creating a function that list out the best possible hyper parameter combination and gives them to you back in a csv file to see whats the best hyper parameters to use for the LDA model. (this took a very long time to run)

# pyLDAvis

We used this vis to see what overlap we had to see if we could better tune the model

# Nearest Neighbor

We then implantment another model Nearest Neighbors for the purposes of outputing the most related jobs to the grad

### Data Sources

https://github.com/Lambda-School-Labs/Job-Funnel-ds-API/blob/master/docs/api/reference.md


## Contributing

When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other method with the owners of this repository before making a change.

Please note we have a [code of conduct](./code_of_conduct.md.md). Please follow it in all your interactions with the project.

### Issue/Bug Request

 **If you are having an issue with the existing project code, please submit a bug report under the following guidelines:**
 - Check first to see if your issue has already been reported.
 - Check to see if the issue has recently been fixed by attempting to reproduce the issue using the latest master branch in the repository.
 - Create a live example of the problem.
 - Submit a detailed bug report including your environment & browser, steps to reproduce the issue, actual and expected outcomes,  where you believe the issue is originating from, and any potential solutions you have considered.

### Feature Requests

We would love to hear from you about new features which would improve this app and further the aims of our project. Please provide as much detail and information as possible to show us why you think your new feature should be implemented.

### Pull Requests

If you have developed a patch, bug fix, or new feature that would improve this app, please submit a pull request. It is best to communicate your ideas with the developers first before investing a great deal of time into a pull request to ensure that it will mesh smoothly with the project.

Remember that this project is licensed under the MIT license, and by submitting a pull request, you agree that your work will be, too.

#### Pull Request Guidelines

- Ensure any install or build dependencies are removed before the end of the layer when doing a build.
- Update the README.md with details of changes to the interface, including new plist variables, exposed ports, useful file locations and container parameters.
- Ensure that your code conforms to our existing code conventions and test coverage.
- Include the relevant issue number, if applicable.
- You may merge the Pull Request in once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you.

### Attribution

These contribution guidelines have been adapted from [this good-Contributing.md-template](https://gist.github.com/PurpleBooth/b24679402957c63ec426).

## Documentation

See [Backend Documentation](https://github.com/Lambda-School-Labs/Job-Funnel-be) for details on the backend of our project.



