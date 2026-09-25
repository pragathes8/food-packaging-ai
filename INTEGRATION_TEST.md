# End-to-end test

1. Start backend on port 8000.
2. Start frontend on port 5173.
3. Confirm the UI says `Engine online`.
4. Select `Tomato`.
5. Click `Generate recommendations`.
6. Confirm three ranked packaging recommendations appear.
7. Select the first recommendation and inspect compatibility, scores, evidence coverage and explanation.

Expected representative backend result: Tomato returns three recommendations and the top candidate is `PET/PE laminate` in the current validated engine output.
