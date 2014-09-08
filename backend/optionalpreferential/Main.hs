{-# LANGUAGE OverloadedStrings #-}
import Database.PostgreSQL.Simple
import Database.PostgreSQL.Simple.FromRow
import Control.Applicative
import Control.Monad
import System.Environment
import System.Exit
import Data.Maybe
import Data.List

prefix = "vote3fe_"

-- break these out into loadable files so other backends can use them
-- election
data Election = Election { electionID :: Int
                         , electionName :: String
                         , electionNotes :: String
                         }

instance FromRow Election where
    fromRow = Election <$> field <*> field <*> field

instance Show Election where
    show e = "Election " ++ (show $ electionID e) ++ ": '" ++ (electionName e) ++ "'"


-- candidate
data Candidate = Candidate { candidateID :: Int
                           , candidateName :: String
                           }

instance FromRow Candidate where
    fromRow = Candidate <$> field <*> field

instance Show Candidate where
    show c = "Candidate " ++ (show $ candidateID c) ++ ": " ++ (candidateName c)

-- ballotentry?
-- data BallotEntry = BallotEntry { electionID :: Int
--                                , candidateID :: Int
--                                , position :: Int
--                                }


-- vote stuff
data VoteRow = VoteRow { voteRowID :: Int
                       , voteRowElectionID :: Int
                       } deriving (Show)

instance FromRow VoteRow where
    fromRow = VoteRow <$> field <*> field

data PreferenceRow = PreferenceRow { preferenceRowCandidateID :: Int
                                   , preferenceRowValue :: Maybe Int
                                   } deriving (Show)

instance FromRow PreferenceRow where
    fromRow = PreferenceRow <$> field <*> field


data Preference = Preference { preferenceCandidate :: Candidate
                             , preferenceValue :: Maybe Int 
                             } deriving (Show)

data Vote = Vote { voteID :: Int
                 , votePreferences :: [Preference]
                 } deriving (Show)


electionByID :: Connection -> Int -> IO Election
electionByID c eid = let q = query c "SELECT * FROM vote3fe_election WHERE id = ?" (Only eid)
                      in liftM head q

candidatesForElection :: Connection -> Election -> IO [Candidate]
candidatesForElection c e = query c "SELECT vote3fe_candidate.* FROM vote3fe_ballotentry JOIN vote3fe_candidate ON vote3fe_ballotentry.candidate_id = vote3fe_candidate.id WHERE vote3fe_ballotentry.election_id = ?" (Only $ electionID e)

voteRowsForElection :: Connection -> Election -> IO [VoteRow]
voteRowsForElection c e = query c "SELECT vote3fe_vote.* FROM vote3fe_vote WHERE vote3fe_vote.election_id = ?" (Only $ electionID e)

preferenceRowsForVoteRow :: Connection -> VoteRow -> IO [PreferenceRow]
preferenceRowsForVoteRow c v = query c "SELECT candidate_id, preference FROM vote3fe_preference WHERE vote_id = ?" (Only $ voteRowID v)

-- create a real vote from the database data
-- converts preferencerows into preferences, discarding preferences for candidates
-- that are not given.
-- That is, if you manage to insert a preference for candidate D, when only A B and C
-- are running, this will discard the preference for D.
voteFromRowsWithCandidates :: [Candidate] -> VoteRow -> [PreferenceRow] -> Vote
voteFromRowsWithCandidates cs v prs = 
  let vid = (voteRowID v)
      candidateIDs = map candidateID cs
      validPRs = filter (\pr -> (preferenceRowCandidateID pr) `elem` candidateIDs) prs
      ps = map (\pr -> Preference (fromJust $ find (\c -> candidateID c == preferenceRowCandidateID pr) cs)
                                  (preferenceRowValue pr))
               
               validPRs
  in Vote vid ps

parse ["-h"] = usage >> exitSuccess
parse []     = usage >> exitFailure
parse [eid]  = return (read eid)
parse _      = usage >> exitFailure

usage = putStrLn "Usage: optionalpreferential [-h] electionID"


main :: IO ()
main = do
   electionid <- getArgs >>= parse
   conn <- connectPostgreSQL "host='localhost' dbname='vote3' user='vote3' password='vote3votingsystempassword'"
   election <- electionByID conn electionid
   candidates <- candidatesForElection conn election
   voterows <- voteRowsForElection conn election
   prefrows <- mapM (preferenceRowsForVoteRow conn) voterows
   let votes = zipWith (voteFromRowsWithCandidates candidates) voterows prefrows
   print votes