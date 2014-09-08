module Vote.Util ( isFormal
                 , isFormalWithTests
                 , highestPreference
                 ) where

import Data.Maybe
import Data.List
import Vote.Types

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
isFormal = isFormalWithTests [strictSequence]

isFormalWithTests :: [(Vote -> Bool)] -> Vote -> Bool
isFormalWithTests tests vote = all (\test -> test vote) tests

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
