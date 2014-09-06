# Vote3 - Online voting with minimal terribleness #

So you want to run an election?

 * With some horribly complicated voting system like optional preferential
 * But in near real time
 * And you're happy to take on the myriad risks involved in online voting?

Then this is the system for you!

# Getting started #

At the moment nothing works. This is for your interest only.

```shell
vagrant up
# this will provision all the necessary dependencies, yay.
# it takes a while. Have a coffee or 3.
vagrant ssh
cd /vagrant
# set yourself up a superuser
cd frontend
source env/bin/activate
cd vote3fe_project
python mange.py createuseruser
# answer the questions
<do stuff>
```

Everything runs inside a self contained vm, running of Ubuntu.

By default the program won't be accessible from outside of the host machine (your machine).

You have a number of options to deal with this:

 * Bridged mode
 * Deploy on the magic internets.

If you deploy on the magic internets, and you use a reverse proxy like nginx (which you probably should!) you'll need to change the `@ratelimit` line in `frontend/vote3fe_project/vote3fe/views.py` to ratelimit against something more appropriate.

# How does it work? #
Vote3 is divided up into two parts, a front end and a back end. Both are pluggable/replaceable/interchangeable.

## Frontend ##
The front end is responsible for collecting votes from people. This is a very loose task, and there are multiple ways to do it.

The supplied front end is a Django web application that allows votes to be collected online.

The returning officer (RO) logs in to the web app, and creates a new election. The RO adds candidates to the election, and states the order those candidates are to appear on the ballot.

The RO then creates 'voting codes'. Voting codes are the tokens that authenticate a voter to the system. So, if the RO expects there will be up to 100 voters, the RO creates 100 tokens, then prints them out, cuts them up, and distributes them to voters.

Voters then take the voting codes and use them to vote. The voting code:

 * Can be used only once.
 * Can authorise the voter to vote in 1 or more elections.

Voting codes can also be created before the candidate list is finalised, which is convenient if you allow nominations on the day.

To provide brute-force resistance, a voting code is 128 bits (16 bytes) of true randomness. This is base64 encoded (to 24 bytes, but it always ends with two equals signs, so they're removed, leaving 22 bytes). Ratelimiting is also enforced.

The front end deliberately does not verify if votes are formal. There are two reasons for this:

 1. The front end is designed to work across as many backends as possible.
 1. The front end is designed to allow voters to vote informally if they desire, because apparently that's a valid way to express yourself in an election.

The one thing that the front end verifies is that if you put a number next to a candidate, the number is actually a number. You can't write "go to hell" next to your least favourite candidate, sorry.

If you want a different feature set, it's easy to write your own. There's only one thing it has to obey, and that's the database schema described below. If you want people to vote via Gopher, go for it.

## Backend ##
Once votes are collected, they must be counted. This is done with a backend. A backend can implement any counting system desired - first past the post, mandatory preferential, optional preferential, Hare-Clark(e?), ad nauseum.

For historical reasons*, vote3 is supplied with two Haskell-based counting systems, optional preferential single-member, and optional preferential multi-member.

These are invoked by the RO from the command line, and print out detailed information about the count, eventually telling you who won, enabling you to welcome your new democratically-elected overlords.

## Database ##
The front and back ends communicate through a database. For various reasons, not least of which is the idea that consistency matters, PostgreSQL is used.

A rough outline to the schema is as follows.

 * Election
     * Election ID
     * Election Name, must be unique
     * Election Notes (information that is displayed to voters. Does *not* enforce anything internally.)

 * Candiate
     * Candidate ID
     * Candidate Name, must be unique (protip: put a year in the election name!)

 * BallotEntry
     * (there may be an internal ID, but we don't care)
     * Election ID
     * Candidate ID (electionID+candidateID must be unique - no-one can run twice in the same election.)
     * Position (electionID+postition must also be unique - no two people can be in the same position.)

For clarity: elections can have many candidates. A candidate could be in multiple elections, but the order of the candidates in each election/on the ballot matters. (This is to allow for example, the double-random process for putting candidates on ballots.)

 * Vote
   * Vote ID
   * Election ID

 * Preference
   * (there may be an internal ID here, but we don't care)
   * Vote ID
   * Candidate ID (VoteID+CandiateID must be unique)
   * Preference - a number, _or nothing_. Does not have *any* restrictions; no formality is to be imposed by the front end or expected by the backend.

For clarity, a vote has many candidate votes, which are basically filled in ballot entries. We could have CandidateVote reference BallotEntry, which would be more in line with normalised design, but I don't do this because that would require the counting software to care about the BallotEntry table, and this way it doesn't. Simple = good.

This arrangement does - in theory - allow you to vote for a candidate that isn't running in the election; we trust the front end not to allow something that brain dead. If we did reference BallotEntry, we'd still need to validate that the ballot entry was actually for the given election. I'm not sure how we could enforce this at the database level, so we both:

 1. hope for the best that the front end enforces it, *and*
 1. make it a design requirement that the backends check this and either do/don't allow write-ins as required.

The following models are *only used by the current front end*; a new front end is not required to implement them, and the backend must not use them. They are written down here because they were written as part of the design process and I see no good reason to remove them. For clarity, elections have many vote codes, and a votecode can authorize voting in mutiple elections - e.g. Pres/VP/Sec/Treas/Committee.

 * VoteCode
     * VoteCode ID
     * VoteCode (as described above, unique)

 * ElectionVoteCodes
     * Election ID
     * VoteCode ID (must be unique together with election ID)
     * Used? (yes/no)

The use is done at the ElectionVotecode level. Previously I considered having it done at the Votecode level, but it made it hard to ensure that a votecode was only used once per election; basically it required me to trust that users couldn't monkey with their sessions and I wasn't willing to do that.

# Acknowledgements #
I'd like to gratefully acknowleged the [cssavote2](https://github.com/anucssa/cssavote2), from which I learned a lot. The existence of vote3 is in no way intended as a criticism of cssavote2.
