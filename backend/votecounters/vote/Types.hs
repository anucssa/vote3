module Vote.Types ( Election (Election, electionID, electionName, electionNotes)
             , Candidate (Candidate, candidateID, candidateName, Exhausted)
             , Preference (Preference, preferenceCandidate, preferenceValue)
             , Vote (Vote, voteID, votePreferences)
             ) where

import Data.List

data Election = Election { electionID :: Int
                         , electionName :: String
                         , electionNotes :: String
                         }


instance Show Election where
    show e = "Election " ++ (show $ electionID e) ++ ": '" ++ (electionName e) ++ "'"


-- candidate
data Candidate = Candidate { candidateID :: Int
                           , candidateName :: String
                           } |
                 Exhausted deriving (Eq)


instance Show Candidate where
    show Exhausted = "Exhausted"
    show c = "Candidate " ++ (show $ candidateID c) ++ ": " ++ (candidateName c)

-- ballotentry?
-- data BallotEntry = BallotEntry { electionID :: Int
--                                , candidateID :: Int
--                                , position :: Int
--                                }

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
