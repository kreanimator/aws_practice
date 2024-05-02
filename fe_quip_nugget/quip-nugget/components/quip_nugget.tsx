"use client";
import React from "react";
import Form from "./form";
import Results from "./results"
import { useState } from "react";

const QuipNugget: React.FC = () => {
    const CHARACTER_LIMIT: number = 32;
    const ENDPOINT: string = "https://gvz6ywtue1.execute-api.us-west-2.amazonaws.com/dev/app/generate_data";
    const [prompt, setPrompt] = React.useState("");
    const [joke, setJoke] = React.useState("");
    const [fact, setFact] = React.useState("");
    const [keywords, setKeywords] = React.useState([]);
    const [hasResult, setHasResult] = React.useState(false);
    const [isLoading, setIsLoading] = React.useState(false);

    const onSubmit = () => {
        console.log("Submitting: " + prompt);
        setIsLoading(true);
        fetch(`${ENDPOINT}?user_input=${prompt}`)
        .then((res) => res.json())
        .then(onResult);
        }
    const onResult = (data: any) => {
        setJoke(data.joke);
        setFact(data.fact);
        setKeywords(data.keywords);
        setHasResult(true);
        setIsLoading(false);
        }
    const onReset = (data: any) => {
        setPrompt("");
        setHasResult(false);
        setIsLoading(false);
        }

    let displayedElement = null;
//         console.log(joke)
//         console.log(fact)
//         console.log(keywords)

    if (hasResult){

        displayedElement = <Results
         prompt={prompt}
         joke={joke}
         fact={fact}
         keywords={keywords}
         onBack={onReset}
         />;
    }else{
        displayedElement = (<Form
            prompt={prompt}
            setPrompt={setPrompt}
            onSubmit={onSubmit}
            isLoading={isLoading}
            characterLimit={CHARACTER_LIMIT}
            />);
        }


    return(
    <>
    <h1><b>Quip Nugget</b></h1>
    {displayedElement}
    </>
    )
    }
export default QuipNugget;