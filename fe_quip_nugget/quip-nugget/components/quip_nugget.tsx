"use client";
import React from "react";
import { useState } from "react";

const QuipNugget: React.FC = () => {

    const [prompt, setPrompt] = React.useState("");
    const onSubmit = () => {
        console.log("Submitting: " + prompt)
        fetch(`https://gvz6ywtue1.execute-api.us-west-2.amazonaws.com/dev/app/generate_data?user_input=${prompt}`)
        }

    return(
    <>
    <h1>Quip Nugget</h1>
    <p>
    What's on your mind? Tell me and I'll try to make a joke for you!
    </p>
    <input
     type="text"
     placeholder="coffee"
     value={prompt}
     onChange={(e) => setPrompt(e.currentTarget.value)}
     ></input>
    <button onClick={onSubmit}>Submit</button>
    </>
    )
    }
export default QuipNugget;