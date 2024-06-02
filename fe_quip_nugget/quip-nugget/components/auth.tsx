import React from "react";

interface AuthProps {
    setIsLoggedIn: React.Dispatch<React.SetStateAction<boolean>>;
}

const Auth: React.FC<AuthProps> = ({ setIsLoggedIn }) => {
    const handleLogin = () => {
        // Simulate login process here
        setIsLoggedIn(true); // Update isLoggedIn state to true
    };

    return (
        <>
            <div className="mb-6 text-slate-400 flex justify-center">
                <p>Please login to continue.</p>
            </div>
            <button
                className="bg-gradient-to-r from-emerald-400 to-emerald-800 disabled:opacity-50 w-full p-2 rounded-md text-lg"
                onClick={handleLogin} // Call handleLogin function when the button is clicked
            >
                Login
            </button>
        </>
    );
};

export default Auth;
