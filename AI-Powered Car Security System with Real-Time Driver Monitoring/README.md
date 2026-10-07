# Car Safety
This is collaboration project that aims to protect users while driving, by detecting of they are tired or not and warning them, also it protects the user's car by performing  a face recognition on the user to see if its car or not or by entering a pin number .
> Note 
> we considered a person is tired if his eyes is closed for 5 seconds 

## How it works 
- **Modules:**
    - `Picamera module:` interacts with the Picamera 
    - `computerVision module :` Face recognition and detction, eyses closed detection
    - `Buzzer module:` wring and sound effects 
    - `LCD module:` display text on LCD 
- **Main program flow:** 
    - `State engine Off:` 
        - detect if `'#'` key was pressed to start engine one 
    - `State engine  On :`
        - before driving user has to authentificate his identity: 
            - detect and recognize faces to start engine 
            - ability to enter a pin code to start engine `'*'`
            - Reset key  `'C'` pin to reset from start
    - `State driving:`
        - detect if eyes are closed for `3s`, if true set state engine to OFF 
        - if `'A'` key is pressed set state to engine OFF 

