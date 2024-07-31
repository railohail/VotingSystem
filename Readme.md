## Install

Go to the votingsys folder and run:

```
npm install
```

Go to the server folder and run:

```
pip install -r requirements.txt
```

## Run

Go to the votingsys folder and run:

```
npm run dev
```

to start the front end

Go to the root folder and run:

```
uvicorn server.pollserver:app --host 0.0.0.0 --port 8000 --reload
```

to start the back end
