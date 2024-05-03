import Share from "./share";

interface ResultsProps{
        prompt: string;
        joke: string;
        fact: string;
        keywords: string[];
        onBack: any;
    }

const Results: React.FC<ResultsProps> = (props) => {

         const keywordElements = [];
          for (let i = 0; i < props.keywords.length; i++) {
            const element = (
              <div
                key={i}
                className="bg-gradient-to-r from-green-300 to-emerald-400 p-1 text-white shadowed-text px-2 text-sm rounded-md"

              >
                {props.keywords[i]}
              </div>
            );
            keywordElements.push(element);
          }
       const keywordElementsHolder = (
        <div className="flex flex-wrap gap-2">{keywordElements}</div>
        );

       const resultSection = (label: string, body: any, color: string) => {
        return (
          <div className={`${color} p-4 my-3 rounded-md`}>
            <div className="text-white text-sm font-bold mb-1" >{label}</div>
            <div>{body}</div>
          </div>
        );
        };

          const shareContent = `Check out this funny prompt: ${props.prompt}\n\nCheck out this joke: ${props.joke}\n\nCheck out this fun fact: ${props.fact}`;


       return (
               <>
                  <div className="mb-6">
                    {resultSection(
                      "Your funny input",
                      <div className="text-lg font-bold">{props.prompt}</div>, "bg-emerald-700"
                    )}
                    {resultSection("Joke", props.joke, "bg-emerald-700")}
                    {resultSection("Funfact", props.fact, "bg-emerald-700")}
                    {resultSection("Keywords", keywordElementsHolder, "bg-emerald-700")}
                  </div>
                  <Share description={shareContent} />

                  <button
                    className="bg-gradient-to-r from-emerald-400
                    to-emerald-800 disabled:opacity-50 w-full p-2 rounded-md text-lg"
                    onClick={props.onBack}
                  >
                    New joke
                  </button>
                </>
    );
};

export default Results;