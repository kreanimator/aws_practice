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
                className="bg-gradient-to-r from-emerald-100 to-emerald-400 p-1 text-teal-700 px-2 text-sm rounded-md"

              >
                #{props.keywords[i]}
              </div>
            );
            keywordElements.push(element);
          }
       const keywordElementsHolder = (
        <div className="flex flex-wrap gap-2">{keywordElements}</div>
        );

       const resultSection = (label: string, body: any) => {
        return (
          <div className="bg-emerald-700 p-4 my-3 rounded-md">
            <div className="text-slate-400 text-sm font-bold mb-4">{label}</div>
            <div>{body}</div>
          </div>
        );
        };

       return (
               <>
                  <div className="mb-6">
                    {resultSection(
                      "Prompt",
                      <div className="text-lg font-bold">{props.prompt}</div>
                    )}
                    {resultSection("Joke", props.joke)}
                    {resultSection("Fact", props.fact)}
                    {resultSection("Keywords", keywordElementsHolder)}
                  </div>
                  <button
                    className="bg-gradient-to-r from-emerald-400
        to-emerald-800 disabled:opacity-50 w-full p-2 rounded-md text-lg"
                    onClick={props.onBack}
                  >
                    Back
                  </button>
                </>
//         <>
//             <div>
//                 <div>
//                     <b>Prompt</b>
//                 </div>
//                 <div>
//                     {props.prompt}
//                 </div>
//                 <div>
//                     <b>Joke</b>
//                 </div>
//                 <div>
//                     {props.joke}
//                 </div>
//                 <div>
//                     <b>Fact</b>
//                 </div>
//                 <div>
//                     {props.fact}
//                 </div>
//                 <div>
//                     <b>Keywords</b>
//                 </div>
//                 <div>
//                     {keywordsElement}
//                 </div>
//             </div>
//             <button
//              className="bg-gradient-to-r from-teal-400
//         to-blue-500 disabled:opacity-50 w-full p-2 rounded-md text-lg"
//              onClick={props.onBack}>Back</button>
//         </>
    );
};

export default Results;