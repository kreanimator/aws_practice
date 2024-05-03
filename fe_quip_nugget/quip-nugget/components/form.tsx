interface FormProps {
    prompt: string;
    setPrompt: any;
    onSubmit: any;
    isLoading: boolean;
    characterLimit: number;

    }

const Form: React.FC<FormProps> = (props) => {

    const isPromptValid = props.prompt.length < props.characterLimit;
    const updatePromptValue = (text: string) => {
        if (text.length <= props.characterLimit){
            props.setPrompt(text)

            }
        };

    let statusColor = "text-slate-500";
    let statusText = null;
    if (!isPromptValid){

        statusColor="text-red-500";
        statusText = `Input must be less than ${props.characterLimit} characters.`;
        }


    return (
        <>
        <div className="mb-6 text-slate-400">
            <p>
                Got something on your mind? Share it, and I'll whip up a witty quip just for you!
            </p>
         </div>
            <input
                className="p-2 w-full rounded-md focus:outline-teal-400 focus:outline text-slate-700"
                type="text"
                placeholder="Knock knock"
                value={props.prompt}
                onChange={(e) => updatePromptValue(e.currentTarget.value)}
            />
            <div className={statusColor + " flex justify-between my-2 mb-6"}>
            <div>{statusText}</div>
            <div>{props.prompt.length}/{props.characterLimit}</div>
            </div>
            <button
            className="bg-gradient-to-r from-teal-400
        to-blue-500 disabled:opacity-50 w-full p-2 rounded-md text-lg"
             onClick={props.onSubmit}
             disabled={props.isLoading || !isPromptValid}>
             Submit</button>
        </>
    );
};
export default Form;