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
                           } |
                 Exhausted deriving (Eq)

instance FromRow Candidate where
    fromRow = Candidate <$> field <*> field

instance Show Candidate where
    show Exhausted = "Exhausted"
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
                             } deriving (Eq)

instance Show Preference where
    show p = (show . candidateName . preferenceCandidate $ p) ++ ": " ++
             (show $ preferenceValue p)

data Vote = Vote { voteID :: Int
                 , votePreferences :: [Preference]
                 }

instance Show Vote where
    show v = "Vote #" ++ (show $ voteID v) ++ ": " ++
             (intercalate "; " $ map show $ votePreferences v)


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


-- Formality tests
-- TODO FIXME
-- These tests do not match any 'official' formality rules!!!
-- in particular, this test, strictSequence, requires the preferences to be
-- 1..n, where n is the number of filled votes. This is overstrict!!
strictSequence :: Vote -> Bool
strictSequence v =
  let filled = filter (isJust . preferenceValue) $ votePreferences v
      hasValue = \x -> isJust $ find (\p -> (preferenceValue p) == Just x) filled
  in (length filled) > 0 && all hasValue [1 .. (length filled)]

isFormal :: Vote -> Bool
isFormal vote = all (\test -> test vote)
                    [strictSequence]


-- Vote Counting!

-- utility
-- return the leading candidate from the given vote, for the remaining pool of candidates, if one exists, otherwise Exhausted
highestPreference :: [Candidate] -> Vote -> Candidate
highestPreference candidates v
  -- no remaining preferences (nothing even recorded; shouldn't occur but can
  -- if DB changes mid voting or new frontend works differently)
  | prefs == [] = Exhausted
  -- all remaining preferences are NULL/Nothing
  | all (isNothing . preferenceValue) prefs = Exhausted
  -- vote is still valid
  | otherwise = let prefValues = map preferenceValue prefs
                    minPref = minimum . catMaybes $ prefValues
                    winningPreference = find (\p -> (preferenceValue p) == Just minPref) prefs
                in preferenceCandidate . fromJust $ winningPreference
  where prefs = filter (\p -> (preferenceCandidate p) `elem` candidates)
                       (votePreferences v)

candidateVoteCounts :: [Candidate] -> [[Vote]] -> [(Candidate, Int)]
candidateVoteCounts candidates votes = 
    zipWith (\c v -> (c, length v)) candidates votes


-- Sort votes into 'piles' by candidate, by highest preference
sortVotesByCandidate :: [Candidate] -> [Vote] -> [[Vote]]
sortVotesByCandidate candidates votes = 
  let votesFor = (\c v -> highestPreference candidates v == c)
   in map (\c -> filter (votesFor c) votes) candidates


-- do we have a winner?
candidateAboveQuota :: Int -> [Candidate] -> [[Vote]] -> Maybe Candidate
candidateAboveQuota quota candidates votes
  | answer == [] = Nothing
  | otherwise    = Just $ fst . head $ answer
  where answer = filter (\(c, v) -> v >= quota) 
                        (candidateVoteCounts candidates votes)

-- who has the fewest votes?
fewestVotes :: [Candidate] -> [[Vote]] -> [Candidate]
fewestVotes candidates votes =
 let cvc = candidateVoteCounts candidates votes
     minVotes = minimum $ map snd cvc
     minCandidates = filter (\(c, v) -> v == minVotes) cvc
 in map fst minCandidates

-- A round of counting
count' :: Int -> [Candidate] -> [[Vote]] -> IO Candidate
count' round candidates votes = do
  putStrLn ""
  putStrLn $ "Beginning Count Round " ++ (show round)
  let numvotes = sum (map length votes)
  let quota = (numvotes `div` 2) + 1
  putStrLn $ "There are " ++ (show numvotes) ++ " votes remaining. The quota is " ++
             (show quota) ++ " votes."
  mapM (\(c, v) -> putStrLn $ (show c) ++ " has " ++ (show v) ++ " votes.") 
       (candidateVoteCounts candidates votes)
  let winner = candidateAboveQuota quota candidates votes
  if isJust winner
   then do
      putStrLn $ (show $ fromJust winner) ++ " has met the quota."
      return $ fromJust winner
    else do
      putStrLn "No one has met quota."
      let eliminationCandidates = fewestVotes candidates votes
      if (length eliminationCandidates) == 1
       then do
         let eliminated = head eliminationCandidates
         putStrLn $ (show eliminated) ++ " is eliminated; distributing votes."
         let idx = fromJust $ elemIndex eliminated candidates
         let candidates' = (delete eliminated candidates) ++ [Exhausted]
         let votes' = fst (splitAt idx votes) ++ snd (splitAt (idx+1) votes)
         let redistributedVotes = votes!!idx
         let distribution = sortVotesByCandidate candidates' redistributedVotes
         mapM (\(c, v) -> putStrLn $ (show v) ++ " votes -> " ++ (show c) ++ ".") 
              (candidateVoteCounts candidates' distribution)
         let votes'' = zipWith (++) votes' distribution
         count' (round + 1) candidates' votes''
       else do
         putStrLn "We have more than one candidate tied for elimination."
         print eliminationCandidates
         putStrLn "This is not yet implemented."
         exitFailure    
         return Exhausted 

-- A full count
count :: [Candidate] -> [Vote] -> IO Candidate
count cs vs = count' 1 cs (sortVotesByCandidate cs vs)

-- 'UI'
parse ["-h"] = usage >> exitSuccess
parse []     = usage >> exitFailure
parse [eid]  = return (read eid)
parse _      = usage >> exitFailure

usage = putStrLn "Usage: optionalpreferential [-h] electionID"


main :: IO ()
main = do
   electionid <- getArgs >>= parse
   putStrLn "Optional Preferential Vote Counter"
   putStrLn "=================================="
   putStrLn ""
   putStrLn $ "I am the optional preferential vote counter. I have been asked to count votes for election " ++ (show electionid) ++ "."
   putStrLn "Connecting to the database."
   conn <- connectPostgreSQL "host='localhost' dbname='vote3' user='vote3' password='vote3votingsystempassword'"
   putStrLn "Fetching the election."
   election <- electionByID conn electionid
   putStrLn "Fetching the candidates."
   candidates <- candidatesForElection conn election
   putStrLn $ "I have " ++ (show $ length candidates) ++ " candidates:"
   print candidates
   putStrLn "Fetching votes." 
   voterows <- voteRowsForElection conn election
   prefrows <- mapM (preferenceRowsForVoteRow conn) voterows
   let votes = zipWith (voteFromRowsWithCandidates candidates) voterows prefrows
   putStrLn $ "I have " ++ (show $ length votes) ++ " votes."
   putStrLn "Sorting votes into formal and informal."
   --print votes
   let formal = filter isFormal votes
   let informal = filter (not . isFormal) votes
   putStrLn $ "I have " ++ (show $ length formal) ++ " formal votes, and " ++
              (show $ length informal) ++ " informal votes."
   result <- count candidates formal
   putStrLn $ "I declare elected: " ++ (show result)