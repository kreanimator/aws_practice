"use client";
import React, { useState, useEffect } from "react";
import Form from "./form";
import Results from "./results";
import Image from "next/image";
import logo from "../public/gold-nugget.png";

const QuipNugget: React.FC = () => {
    const CHARACTER_LIMIT: number = 32;
    const ENDPOINT: string = "https://gvz6ywtue1.execute-api.us-west-2.amazonaws.com/dev/app/generate_data";
    const [prompt, setPrompt] = useState("");
    const [joke, setJoke] = useState("");
    const [fact, setFact] = useState("");
    const [keywords, setKeywords] = useState([]);
    const [hasResult, setHasResult] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        console.log("Component mounted");
        // Initial logging to understand the component's initial state
        console.log({ joke, fact, keywords, hasResult, isLoading });
    }, []);

    const onSubmit = async () => {
        console.log("Submitting: " + prompt);
        setIsLoading(true);

        // Set timeout value in milliseconds (e.g., 10 seconds)
        const timeout = 10000;

        fetch(`${ENDPOINT}?user_input=${prompt}`, { timeout: timeout } as any)
            .then((res) => {
                if (!res.ok) {
                    throw new Error("Network response was not ok");
                    console.log("Response status:", res.status);
                }
                return res.json();
            })
            .then(onResult)
            .catch((error) => {
                console.error("Error fetching data:", error);
                setIsLoading(false);
            });
    };



    const onResult = (data: any) => {
        console.log("Received data:", data);
        setJoke(data.joke || "");
        setFact(data.fact || "");
        setKeywords(data.keywords || []);
        setHasResult(true);
        setIsLoading(false);
    }

    const onReset = () => {
        setPrompt("");
        setHasResult(false);
        setIsLoading(false);
        console.log("Resetting state");
        // Logging state reset
        console.log({ joke, fact, keywords, hasResult, isLoading });
    }

    let displayedElement = null;

    if (hasResult) {
        displayedElement = (
            <Results
                prompt={prompt}
                joke={joke}
                fact={fact}
                keywords={keywords}
                onBack={onReset}
            />
        );
    } else {
        displayedElement = (
            <Form
                prompt={prompt}
                setPrompt={setPrompt}
                onSubmit={onSubmit}
                isLoading={isLoading}
                characterLimit={CHARACTER_LIMIT}
            />
        );
    }

    const gradientTextStyle = "text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-emerald-950 font-light w-fit mx-auto";

    return (
        <div className="h-screen flex justify-center items-center">
            <div className="max-w-md m-auto p-2">
                <div className="bg-teal-50 p-6 rounded-md text-slate-300">
                    <div className="text-center my-6">
                        <Image src={logo} width={64} height={64} alt="Quip Nugget logo" style={{ display: 'block', margin: '0 auto' }} />
                        <h1 className={gradientTextStyle + " text-3xl font-light w-fit mx-auto"}>Quip Nugget</h1>
                        <div className={gradientTextStyle}>Where wit takes flight from your fingertips!</div>
                    </div>
                    {displayedElement}
                </div>
                <footer className="text-gray-500 text-center my-6">project by <a href="https://github.com/kreanimator" className="underline">kreanimator</a></footer>
                <footer className="text-gray-500 text-center my-6">powered by <a href="https://docs.sosw.app/" className="underline">SOSW</a></footer>
            </div>
        </div>
    );
}

export default QuipNugget;
