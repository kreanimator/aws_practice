interface ResultsProps{
        prompt: string;
        joke: string;
        fact: string;
        keywords: string[];
        onBack: any;
    }

const Results: React.FC.<ResultsProps> = (props) => {

       const keywordsElement = [];
       for (let i = 0; i < props.keywords.length; i++){

           const element = <div key={i}>#{props.keywords[i]}</div>;
           keywordsElement.push(element);
           }

       return (
        <>
            <div>
                <div>
                    <b>Prompt</b>
                </div>
                <div>
                    {props.prompt}
                </div>
                <div>
                    <b>Joke</b>
                </div>
                <div>
                    {props.joke}
                </div>
                <div>
                    <b>Fact</b>
                </div>
                <div>
                    {props.fact}
                </div>
                <div>
                    <b>Keywords</b>
                </div>
                <div>
                    {keywordsElement}
                </div>
            </div>
            <button onClick={props.onBack}>Back</button>
        </>
    );
};

export default Results;