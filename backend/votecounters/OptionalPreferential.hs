{-# LANGUAGE OverloadedStrings #-}
import Control.Monad
import System.Environment
import System.Exit
import Data.Maybe
import Data.List
import Vote.Types
import Vote.Database
import Vote.Util


-- Vote Counting!
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
   votes <- votesForCandidatesForElection conn election candidates
   putStrLn $ "I have " ++ (show $ length votes) ++ " votes."
   putStrLn "Sorting votes into formal and informal."
   --print votes
   let formal = filter isFormal votes
   let informal = filter (not . isFormal) votes
   putStrLn $ "I have " ++ (show $ length formal) ++ " formal votes, and " ++
              (show $ length informal) ++ " informal votes."
   result <- count candidates formal
   putStrLn $ "I declare elected: " ++ (show result)